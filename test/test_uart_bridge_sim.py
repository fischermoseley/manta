from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out
from cobs import cobs

from manta import *
from manta.uart import UARTInterface
from manta.utils import *


class UARTHardwarePlusMemoryCore(wiring.Component):
    rx: In(1)
    tx: Out(1)

    def elaborate(self, platform):
        m = Module()
        m.submodules.uart = uart = UARTInterface(
            port="None",
            baudrate=1e6,
            clock_freq=10e6,
        )
        m.submodules.mem_core = mem_core = MemoryCore("bidirectional", 32, 1024)
        mem_core.base_addr = 0

        # Expose the UARTInterface externally, so tests can grab
        # the _clocks_per_baud attribute
        self.uart = uart

        wiring.connect(m, uart.bus_source, mem_core.bus_sink)
        wiring.connect(m, mem_core.bus_source, uart.bus_sink)

        m.d.comb += self.tx.eq(uart.tx)
        m.d.comb += uart.rx.eq(self.rx)

        return m


uart_hw = UARTHardwarePlusMemoryCore()


async def send_byte(ctx, module, data):
    # 8N1 serial, LSB sent first
    data_bits = "0" + f"{data:08b}"[::-1] + "1"
    data_bits = [int(bit) for bit in data_bits]

    for i in range(10 * uart_hw.uart._clocks_per_baud):
        bit_index = i // uart_hw.uart._clocks_per_baud
        ctx.set(module.rx, data_bits[bit_index])
        await ctx.tick()


@simulate(uart_hw)
async def test_read_request(ctx):
    addr = 0x5678_9ABC
    header = EthernetMessageHeader.from_params(MessageTypes.READ_REQUEST, seq_num=0x0, length=1)
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
