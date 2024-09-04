import os

import pytest
from amaranth import *
from amaranth.lib import io
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from manta import *
from manta.utils import *


class LogicAnalyzerCounterTest(Elaboratable):
    def __init__(self, platform, port):
        self.platform = platform
        self.port = port

    def elaborate(self, platform):
        # Since we know that all the tests will be called only after the FPGA
        # is programmed, we can just push all the wiring into the elaborate
        # method, instead of needing to define Manta in the __init__() method

        probe0 = Signal()
        probe1 = Signal(3)
        probe2 = Signal(9)

        self.manta = manta = Manta()
        manta.interface = UARTInterface(
            port=self.port, baudrate=3e6, clock_freq=platform.default_clk_frequency
        )
        manta.cores.la = LogicAnalyzerCore(
            sample_depth=1024, probes=[probe0, probe1, probe2]
        )

        m = Module()
        m.submodules.manta = manta

        uart_pins = platform.request("uart", dir={"tx": "-", "rx": "-"})
        m.submodules.uart_rx = uart_rx = io.Buffer("i", uart_pins.rx)
        m.submodules.uart_tx = uart_tx = io.Buffer("o", uart_pins.tx)

        m.d.sync += probe0.eq(probe0 + 1)
        m.d.sync += probe1.eq(probe1 + 1)
        m.d.sync += probe2.eq(probe2 + 1)

        m.d.comb += [
            self.manta.interface.rx.eq(uart_rx.i),
            uart_tx.o.eq(self.manta.interface.tx),
        ]

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def verify(self):
        self.build_and_program()

        self.manta.cores.la.triggers = ["probe0 EQ 0"]
        cap = self.manta.cores.la.capture()

        make_build_dir_if_it_does_not_exist_already()

        # check that VCD export works
        cap.export_vcd("build/logic_analyzer_capture.vcd")

        # check that CSV export works
        cap.export_csv("build/logic_analyzer_capture.csv")

        # check that Verilog export works
        cap.export_playback_verilog("build/logic_analzyer_capture_playback.v")

        # verify that each signal is just a counter modulo the width of the signal
        for p in self.manta.cores.la._probes:
            trace = cap.get_trace(p.name)

            for i in range(len(trace) - 1):
                if trace[i + 1] != (trace[i] + 1) % (2 ** len(p)):
                    raise ValueError("Bad counter!")


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_logic_analyzer_core_xilinx():
    port = os.environ["NEXYS4DDR_PORT"]
    LogicAnalyzerCounterTest(Nexys4DDRPlatform(), port).verify()


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_logic_analyzer_core_ice40():
    port = os.environ["ICESTICK_PORT"]
    LogicAnalyzerCounterTest(ICEStickPlatform(), port).verify()
