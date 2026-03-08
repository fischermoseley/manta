import random

from amaranth import *
from cobs import cobs

from manta import *
from manta.ethernet.bridge import EthernetBridge
from manta.uart.cobs_decode import COBSDecode
from manta.uart.cobs_encode import COBSEncode
from manta.uart.stream_packer import StreamPacker
from manta.uart.stream_unpacker import StreamUnpacker
from manta.utils import *

# Since it takes so many simulation clock cycles to send data in and out,
# it's handy to test the UART datapath without the transmitter/receiver modules,
# and just leave it 8 bits wide on both ends. That's what this testbench does


class UARTDatapath(wiring.Component):
    sink: In(StreamSignature(8, has_last=False))
    source: Out(StreamSignature(8))

    bus_source: Out(InternalBusSignature)
    bus_sink: In(InternalBusSignature)

    def elaborate(self, platform):
        m = Module()

        m.submodules.cobs_decode = cobs_decode = COBSDecode()
        m.submodules.stream_packer = stream_packer = StreamPacker()
        m.submodules.bridge = bridge = EthernetBridge()
        m.submodules.stream_unpacker = stream_unpacker = StreamUnpacker()
        m.submodules.cobs_encode = cobs_encode = COBSEncode()

        wiring.connect(m, wiring.flipped(self.sink), cobs_decode.sink)
        wiring.connect(m, cobs_decode.source, stream_packer.sink)
        wiring.connect(m, stream_packer.source, bridge.sink)
        wiring.connect(m, bridge.source, stream_unpacker.sink)
        wiring.connect(m, stream_unpacker.source, cobs_encode.sink)
        wiring.connect(m, cobs_encode.source, wiring.flipped(self.source))

        wiring.connect(m, bridge.bus_source, wiring.flipped(self.bus_source))
        wiring.connect(m, wiring.flipped(self.bus_sink), bridge.bus_sink)

        return m


class UARTDatapathPlusMemoryCore(wiring.Component):
    sink: In(StreamSignature(8, has_last=False))
    source: Out(StreamSignature(8))

    def elaborate(self, platform):
        m = Module()

        m.submodules.dp = dp = UARTDatapath()
        m.submodules.mem = mem = MemoryCore(mode="bidirectional", width=32, depth=512)
        mem.base_addr = 0

        wiring.connect(m, dp.bus_source, mem.bus_sink)
        wiring.connect(m, mem.bus_source, dp.bus_sink)

        wiring.connect(m, dp.source, wiring.flipped(self.source))
        wiring.connect(m, wiring.flipped(self.sink), dp.sink)

        return m


dpmc = UARTDatapathPlusMemoryCore()


@simulate(dpmc)
async def test_uart_read_request(ctx):
    await read_request(ctx, seq_num=0, addr=0, length=4)
    await write_request(
        ctx, seq_num=1, addr=0, data=[0x1111_1111, 0x2222_2222, 0x3333_3333, 0x4444_4444]
    )
    await read_request(ctx, seq_num=2, addr=0, length=4)


async def read_request(ctx, seq_num, addr, length):
    header = EthernetMessageHeader.from_params(MessageTypes.READ_REQUEST, seq_num, length)
    request = bytestring_from_ints([header.as_bits(), addr], byteorder="little")
    await send_request(ctx, request)


async def write_request(ctx, seq_num, addr, data):
    header = EthernetMessageHeader.from_params(MessageTypes.WRITE_REQUEST, seq_num)
    request = bytestring_from_ints([header.as_bits(), addr, *data], byteorder="little")
    await send_request(ctx, request)


async def send_request(ctx, request):
    request_encoded = cobs.encode(request) + int(0).to_bytes(1)
    response_encoded = await send_and_receive(
        ctx, request_encoded, tx_irritate=False, rx_irritate=False
    )
    response = cobs.decode(bytes(response_encoded[:-1]))  # remove zero delimiter

    hex_print = lambda data: " ".join([f"{d:02x}" for d in data])

    print(
        "\n"
        f" request (unencoded): {hex_print(request)}\n"
        f" request   (encoded): {hex_print(request_encoded)}\n"
        f" response: (encoded): {hex_print(response_encoded)}\n"
        f" response: (decoded): {hex_print(response)}\n"
    )


async def send_and_receive(ctx, data, tx_irritate, rx_irritate):
    await ctx.tick().repeat(5)

    tx_done = False
    tx_index = 0
    rx_done = False
    rx_buf = []

    ctx.set(dpmc.source.ready, 1)
    await ctx.tick()

    while not (tx_done and rx_done):
        # Feed data to decoder
        tx_stall = random.randint(0, 1) if tx_irritate else False

        if tx_done or tx_stall:
            ctx.set(dpmc.sink.data, 0)
            ctx.set(dpmc.sink.valid, 0)

        else:
            ctx.set(dpmc.sink.valid, 1)
            ctx.set(dpmc.sink.data, data[tx_index])

            if ctx.get(dpmc.sink.valid) and ctx.get(dpmc.sink.ready):
                if tx_index == len(data) - 1:
                    tx_done = True

                else:
                    tx_index += 1

        # Randomly set source.ready if irritator is enabled
        ready = random.randint(0, 1) if rx_irritate else 1
        ctx.set(dpmc.source.ready, ready)

        # Pull output data from buffer
        if ctx.get(dpmc.source.valid) and ctx.get(dpmc.source.ready):
            rx_buf += [ctx.get(dpmc.source.data)]

            if ctx.get(dpmc.source.last):
                rx_done = True

        await ctx.tick()

    await ctx.tick().repeat(5)
    return rx_buf
