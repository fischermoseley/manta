from amaranth import *
from cobs import cobs

from manta import *
from manta.ethernet.bridge import EthernetBridge
from manta.uart.cobs_decode import COBSDecode
from manta.uart.cobs_encode import COBSEncode
from manta.uart.receiver import UARTReceiver
from manta.uart.stream_packer import StreamPacker
from manta.uart.stream_unpacker import StreamUnpacker
from manta.uart.transmitter import UARTTransmitter
from manta.utils import *

# uart_rx -> COBS decode -> pack_stream -> bridge -> unpack_stream -> COBS encode -> uart_tx


class UARTHardware(Elaboratable):
    def __init__(self):
        self.rx = Signal()
        self.tx = Signal()

        self.bus_o = Signal(InternalBus())
        self.bus_i = Signal(InternalBus())
        self._clocks_per_baud = 10

    def elaborate(self, platform):
        m = Module()

        m.submodules.uart_rx = uart_rx = UARTReceiver(self._clocks_per_baud)
        m.submodules.cobs_decode = cobs_decode = COBSDecode()
        m.submodules.stream_packer = stream_packer = StreamPacker()
        m.submodules.bridge = bridge = EthernetBridge()
        m.submodules.stream_unpacker = stream_unpacker = StreamUnpacker()
        m.submodules.cobs_encode = cobs_encode = COBSEncode()
        m.submodules.uart_tx = uart_tx = UARTTransmitter(self._clocks_per_baud)

        wiring.connect(m, uart_rx.source, cobs_decode.sink)
        wiring.connect(m, cobs_decode.source, stream_packer.sink)
        wiring.connect(m, stream_packer.source, bridge.sink)
        wiring.connect(m, bridge.source, stream_unpacker.sink)
        wiring.connect(m, stream_unpacker.source, cobs_encode.sink)
        wiring.connect(m, cobs_encode.source, uart_tx.sink)

        m.d.comb += [
            uart_rx.rx.eq(self.rx),
            self.tx.eq(uart_tx.tx),
            self.bus_o.eq(bridge.bus_o),
            bridge.bus_i.eq(self.bus_i),
        ]

        return m


class UARTHardwarePlusMemoryCore(Elaboratable):
    def __init__(self):
        self.rx = Signal()
        self.tx = Signal()

        self._clocks_per_baud = 10

    def elaborate(self, platform):
        m = Module()
        m.submodules.uart = uart = UARTHardware()
        m.submodules.mem_core = mem_core = MemoryCore("bidirectional", 32, 1024)
        mem_core.base_addr = 0

        m.d.comb += uart.bus_i.eq(mem_core.bus_o)
        m.d.comb += mem_core.bus_i.eq(uart.bus_o)

        m.d.comb += [
            self.tx.eq(uart.tx),
            uart.rx.eq(self.rx),
        ]

        return m


uart_hw = UARTHardwarePlusMemoryCore()


async def send_byte(ctx, module, data):
    # 8N1 serial, LSB sent first
    data_bits = "0" + f"{data:08b}"[::-1] + "1"
    data_bits = [int(bit) for bit in data_bits]

    for i in range(10 * uart_hw._clocks_per_baud):
        bit_index = i // uart_hw._clocks_per_baud
        ctx.set(module.rx, data_bits[bit_index])
        await ctx.tick()


@simulate(uart_hw)
async def test_read_request(ctx):
    addr = 0x5678_9ABC
    header = EthernetMessageHeader.from_params(
        MessageTypes.READ_REQUEST, seq_num=0x0, length=1
    )
    request = bytestring_from_ints([header.as_bits(), addr], byteorder="little")
    encoded = cobs.encode(request)
    encoded = encoded + int(0).to_bytes(1)

    ctx.set(uart_hw.rx, 1)
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()

    for byte in encoded:
        await send_byte(ctx, uart_hw, int(byte))
        print(hex(int(byte)))

    await ctx.tick()
