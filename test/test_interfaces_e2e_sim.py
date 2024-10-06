# the purpose of this test is to vet the

# uart_rx -> cobs decode -> bridge -> core chain -> cobs encode -> uart_tx pipeline

from amaranth import *
from manta.uart import UARTReceiver, UARTTransmitter, ReceiveBridge, TransmitBridge
from manta import IOCore
from manta.cobs import COBSEncoder, COBSDecoder
from manta.utils import *


class EndToEndInterfaceTest(Elaboratable):
    def __init__(self):
        self.uart_rx = UARTReceiver(clocks_per_baud=2)
        self.cobs_decoder = COBSDecoder()
        self.bridge_rx = ReceiveBridge()

        # wow this is so ugly
        dummy_signal = Signal()
        self.io_core = IOCore(inputs = [dummy_signal])
        self.io_core.base_addr = 0
        _ = self.io_core.max_addr

        self.bridge_tx = TransmitBridge()

    def elaborate(self, platform):

        m = Module()

        m.submodules.uart_rx = uart_rx = self.uart_rx
        m.submodules.cobs_decoder = cobs_decoder = self.cobs_decoder
        m.submodules.bridge_rx = bridge_rx = self.bridge_rx

        m.submodules.io_core = io_core = self.io_core

        m.submodules.bridge_tx = bridge_tx = self.bridge_tx

        m.d.comb += [
            cobs_decoder.data_in.eq(uart_rx.data_o),
            cobs_decoder.data_in_valid.eq(uart_rx.valid_o),

            bridge_rx.data_i.eq(cobs_decoder.data_out),
            bridge_rx.valid_i.eq(cobs_decoder.data_out_valid),

            io_core.bus_i.addr.eq(bridge_rx.addr_o),
            io_core.bus_i.data.eq(bridge_rx.data_o),
            io_core.bus_i.rw.eq(bridge_rx.rw_o),
            io_core.bus_i.valid.eq(bridge_rx.valid_o),

            bridge_tx.data_i.eq(io_core.bus_o.data),
            bridge_tx.rw_i.eq(io_core.bus_o.rw),
            bridge_tx.valid_i.eq(io_core.bus_o.valid),

        ]

        return m

e2e_interface_test = EndToEndInterfaceTest()


@simulate(e2e_interface_test)
async def test_send_some_bytes(ctx):
    ctx.set(e2e_interface_test.uart_rx.rx, 1)
    await ctx.tick()

    datas = [0x00, 0x08, 0x52, 0x31, 0x32, 0x33, 0x34, 0x0d, 0x0a, 0x00]

    for data in datas:
        await send_byte_uart(ctx, data)


async def send_byte_uart(ctx, data):
    # 8N1 serial, LSB sent first
    data_bits = "0" + f"{data:08b}"[::-1] + "1"
    data_bits = [int(bit) for bit in data_bits]

    for i in range(10 * e2e_interface_test.uart_rx._clocks_per_baud):
        bit_index = i // e2e_interface_test.uart_rx._clocks_per_baud

        ctx.set(e2e_interface_test.uart_rx.rx, data_bits[bit_index])
        await ctx.tick()