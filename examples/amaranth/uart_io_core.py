from time import sleep

from amaranth import *
from amaranth.lib import io
from manta import *


class UARTIOCoreExample(Elaboratable):
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

        # Autodetect the number of LEDs on the platform
        resources = platform.resources.keys()
        self.n_leds = max([i for name, i in resources if name == "led"])

        # Add IOCore to Manta instance
        self.leds = Signal(self.n_leds)
        self.manta.cores.io = IOCore(outputs=[self.leds])

    def elaborate(self, platform):
        m = Module()

        # Add Manta as a submodule
        m.submodules.manta = self.manta

        # Wire each LED to Manta's IO Core output
        for i in range(self.n_leds):
            led = io.Buffer("o", platform.request("led", i, dir="-"))
            m.d.comb += led.o.eq(self.leds[i])
            m.submodules += led

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
        while True:
            self.manta.cores.io.set_probe("leds", 1 << i)
            i = (i + 1) % self.n_leds
            sleep(0.1)


# Amaranth has a built-in build system, and well as a set of platform
# definitions for a huge number of FPGA boards. The class defined above is
# very generic, as it specifies a design independent of any particular FGPA
# board. This means that by changing which platform you pass UARTIOCoreExample
# below, you can port this example to any FPGA board!

if __name__ == "__main__":
    from amaranth_boards.icestick import ICEStickPlatform

    UARTIOCoreExample(platform=ICEStickPlatform(), port="auto").test()
