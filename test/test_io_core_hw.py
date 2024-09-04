import os
from random import getrandbits

import pytest
from amaranth import *
from amaranth.lib import io
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from manta import *
from manta.utils import *


class IOCoreLoopbackTest(Elaboratable):
    def __init__(self, platform, port):
        self.platform = platform
        self.port = port

    def elaborate(self, platform):
        # Since we know that all the tests will be called only after the FPGA
        # is programmed, we can just push all the wiring into the elaborate
        # method, instead of needing to define Manta in the __init__() method

        probe0 = Signal()
        probe1 = Signal(2)
        probe2 = Signal(8)
        probe3 = Signal(20)

        probe4 = Signal(init=1)
        probe5 = Signal(2, init=2)
        probe6 = Signal(8)
        probe7 = Signal(20, init=65538)

        self.manta = manta = Manta()
        manta.cores.io = IOCore(
            inputs=[probe0, probe1, probe2, probe3],
            outputs=[probe4, probe5, probe6, probe7],
        )
        manta.interface = UARTInterface(
            port=self.port, baudrate=3e6, clock_freq=platform.default_clk_frequency
        )

        m = Module()
        m.submodules.manta = manta

        uart_pins = platform.request("uart", dir={"tx": "-", "rx": "-"})
        m.submodules.uart_rx = uart_rx = io.Buffer("i", uart_pins.rx)
        m.submodules.uart_tx = uart_tx = io.Buffer("o", uart_pins.tx)

        m.d.comb += [
            probe0.eq(probe4),
            probe1.eq(probe5),
            probe2.eq(probe6),
            probe3.eq(probe7),
            manta.interface.rx.eq(uart_rx.i),
            uart_tx.o.eq(manta.interface.tx),
        ]

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def verify_output_probe_initial_values(self):
        """
        Test that all output probes take their expected initial values.
        We can't really test for the same of input probes, since the
        strobe register pulses every time the get_probe() method is called.
        """

        for p in self.manta.cores.io._outputs:
            measured = self.manta.cores.io.get_probe(p)
            if measured != p.init:
                raise ValueError(
                    f"Output probe {p.name} took initial value of {measured} instead of {p.init}."
                )

    def verify_probes_update(self):
        """
        This design ties all the output probes to input probes, so this
        test sets the outputs to random values, and verifies the inputs match
        """
        inputs = self.manta.cores.io._inputs
        outputs = self.manta.cores.io._outputs

        # The config is specified in such a way that the first output is
        # connected to the first output, the second output is connected
        # to the second input, and so on...
        for i, o in zip(inputs, outputs):
            value = getrandbits(len(i))

            self.manta.cores.io.set_probe(o, value)
            readback = self.manta.cores.io.get_probe(i)

            if readback != value:
                raise ValueError(
                    f"Reading {o.name} through {i.name} yielded {readback} instead of {value}!"
                )

            else:
                print(
                    f"Reading {o.name} through {i.name} yielded {readback} as expected."
                )

    def verify(self):
        self.build_and_program()
        self.verify_output_probe_initial_values()
        self.verify_probes_update()


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_output_probe_initial_values_xilinx():
    port = os.environ["NEXYS4DDR_PORT"]
    IOCoreLoopbackTest(Nexys4DDRPlatform(), port).verify()


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_output_probe_initial_values_ice40():
    port = os.environ["ICESTICK_PORT"]
    IOCoreLoopbackTest(ICEStickPlatform(), port).verify()
