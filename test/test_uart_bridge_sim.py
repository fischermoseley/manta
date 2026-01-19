from amaranth import *

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

        m.d.comb += [
            uart_rx.rx.eq(self.rx),
            cobs_decode.data_i.eq(uart_rx.data_o),
            cobs_decode.valid_i.eq(uart_rx.valid_o),
            stream_packer.data_i.eq(cobs_decode.data_o),
            stream_packer.valid_i.eq(cobs_decode.valid_o),
            stream_packer.last_i.eq(cobs_decode.last_o),
            bridge.data_i.eq(stream_packer.data_o),
            stream_packer.ready_i.eq(bridge.ready_o),
            bridge.valid_i.eq(stream_packer.valid_o),
            bridge.last_i.eq(stream_packer.last_o),
            stream_unpacker.data_i.eq(bridge.data_o),
            bridge.ready_i.eq(stream_unpacker.ready_o),
            stream_unpacker.valid_i.eq(bridge.valid_o),
            stream_unpacker.last_i.eq(bridge.last_o),
            cobs_encode.data_i.eq(stream_unpacker.data_o),
            cobs_encode.valid_i.eq(stream_unpacker.valid_o),
            # not quite sure what the rest of these signals will be...
            uart_tx.data_i.eq(cobs_encode.data_o),
            uart_tx.start_i.eq(cobs_encode.valid_o),
            cobs_encode.ready_i.eq(uart_tx.done_o),
            self.tx.eq(uart_tx.tx),
            self.bus_o.eq(bridge.bus_o),
            bridge.bus_i.eq(self.bus_i),
        ]

        return m


uart_hw = UARTHardware()


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
    await send_byte(ctx, uart_hw, 0)
    await ctx.tick()
