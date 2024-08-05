from amaranth import *
from amaranth.lib import io
from manta import *
from time import sleep


class UARTLogicAnalyzerExample(Elaboratable):
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

        self.probe0 = Signal(1)
        self.probe1 = Signal(2)
        self.probe2 = Signal(3)
        self.probe3 = Signal(4)

        self.manta.cores.la = LogicAnalyzerCore(
            sample_depth=2048,
            probes=[self.probe0, self.probe1, self.probe2, self.probe3],
        )

    def elaborate(self, platform):
        m = Module()

        # Add Manta as a submodule
        m.submodules.manta = self.manta

        counter = Signal(10)
        m.d.sync += counter.eq(counter + 1)
        m.d.comb += self.probe0.eq(counter[0])
        m.d.comb += self.probe1.eq(counter[1:2])
        m.d.comb += self.probe2.eq(counter[3:5])
        m.d.comb += self.probe3.eq(counter[6:])

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

        # Take a capture
        self.manta.cores.la.trigger_mode = TriggerModes.IMMEDIATE
        cap = self.manta.cores.la.capture()
        cap.export_vcd("capture.vcd")
        cap.export_csv("capture.csv")
        cap.export_playback_verilog("capture.v")


# Amaranth has a built-in build system, and well as a set of platform
# definitions for a huge number of FPGA boards. The class defined above is
# very generic, as it specifies a design independent of any particular FGPA
# board. This means that by changing which platform you pass UARTIOCoreExample
# below, you can port this example to any FPGA board!

if __name__ == "__main__":
    from amaranth_boards.icestick import ICEStickPlatform

    UARTLogicAnalyzerExample(platform=ICEStickPlatform(), port="auto").test()
