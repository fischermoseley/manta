from amaranth import *
from amaranth.lib import io
from manta import *


class UARTMemoryCoreExample(Elaboratable):
    def __init__(self, platform, port):
        self.platform = platform

        # Create Manta instance
        self.manta = Manta()

        # Configure it to communicate over Ethernet
        self.manta.interface = UARTInterface(
            port=port,
            baudrate=2000000,
            clock_freq=platform.default_clk_frequency,
        )

        # Add IOCore to Manta instance
        self.manta.cores.mem = MemoryCore(mode="host_to_fpga", width=16, depth=512)

    def elaborate(self, platform):
        m = Module()

        # Add Manta as a submodule
        m.submodules.manta = self.manta

        # Wire each LED to the data output of the memory core
        for i in range(16):
            led = io.Buffer("o", platform.request("led", i, dir="-"))
            m.d.comb += led.o.eq(self.manta.cores.mem.user_data_out[i])
            m.submodules += led

        # Wire each switch to the address input of the memory core
        for i in range(9):
            sw = io.Buffer("i", platform.request("switch", i, dir="-"))
            m.d.comb += self.manta.cores.mem.user_addr[i].eq(sw.i)
            m.submodules += sw

        # Wire UART pins to the Manta instance
        uart_pins = platform.request("uart", dir={"tx": "-", "rx": "-"})
        m.submodules.uart_rx = uart_rx = io.Buffer("i", uart_pins.rx)
        m.submodules.uart_tx = uart_tx = io.Buffer("o", uart_pins.tx)
        m.d.comb += self.manta.interface.rx.eq(uart_rx.i)
        m.d.comb += uart_tx.o.eq(self.manta.interface.tx)

        return m

    def test(self):
        # Build and program the FPGA
        self.platform.build(self, do_program=True)

        # Iterate through all the LEDs, blinking them off and on
        i = 0
        for i in range(512):
            self.manta.cores.mem.write(i, i)


# Amaranth has a built-in build system, and well as a set of platform
# definitions for a huge number of FPGA boards. The class defined above is
# very generic, as it specifies a design independent of any particular FGPA
# board. This means that by changing which platform you pass UARTIOCoreExample
# below, you can port this example to any FPGA board!

if __name__ == "__main__":
    from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

    UARTMemoryCoreExample(
        platform=Nexys4DDRPlatform(),
        port="auto",
    ).test()
