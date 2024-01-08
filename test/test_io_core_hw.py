from amaranth import *
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform
from amaranth_boards.icestick import ICEStickPlatform
from manta import Manta
from manta.utils import *
import pytest
from random import randint


class IOCoreLoopbackTest(Elaboratable):
    def __init__(self, platform, port):
        self.platform = platform
        self.port = port

        self.config = self.platform_specific_config()
        self.m = Manta(self.config)

    def platform_specific_config(self):
        return {
            "cores": {
                "io_core": {
                    "type": "io",
                    "inputs": {"probe0": 1, "probe1": 2, "probe2": 8, "probe3": 20},
                    "outputs": {
                        "probe4": {"width": 1, "initial_value": 1},
                        "probe5": {
                            "width": 2,
                            "initial_value": 2,
                        },
                        "probe6": 8,
                        "probe7": {"width": 20, "initial_value": 65538},
                    },
                }
            },
            "uart": {
                "port": self.port,
                "baudrate": 3e6,
                "clock_freq": self.platform.default_clk_frequency,
            },
        }

    def elaborate(self, platform):
        m = Module()
        m.submodules["manta"] = self.m

        uart_pins = platform.request("uart")

        m.d.comb += [
            self.m.io_core.probe0.eq(self.m.io_core.probe4),
            self.m.io_core.probe1.eq(self.m.io_core.probe5),
            self.m.io_core.probe2.eq(self.m.io_core.probe6),
            self.m.io_core.probe3.eq(self.m.io_core.probe7),
            self.m.interface.rx.eq(uart_pins.rx.i),
            uart_pins.tx.o.eq(self.m.interface.tx),
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

        # Test that all output probes take their initial values
        inputs = self.config["cores"]["io_core"]["inputs"]
        outputs = self.config["cores"]["io_core"]["outputs"]

        for name, attrs in outputs.items():
            actual = self.m.io_core.get_probe(name)

            if isinstance(attrs, dict):
                if "initial_value" in attrs:
                    expected = attrs["initial_value"]

            else:
                expected = 0

            if actual != expected:
                raise ValueError(
                    f"Output probe {name} took initial value of {actual} instead of {expected}."
                )

    def verify_probes_update(self):
        """
        This design ties all the output probes to input probes, so this
        test sets the outputs to random values, and verifies the inputs match
        """
        inputs = self.config["cores"]["io_core"]["inputs"]
        outputs = self.config["cores"]["io_core"]["outputs"]

        # The config is specified in such a way that the first output is
        # connected to the first output, the second output is connected
        # to the second input, and so on...
        for input, output in zip(inputs, outputs):
            width = self.config["cores"]["io_core"]["inputs"][input]
            value = randint(0, 2**width - 1)

            self.m.io_core.set_probe(output, value)
            readback = self.m.io_core.get_probe(input)

            if readback != value:
                raise ValueError(
                    f"Reading {output} through {input} yielded {readback} instead of {value}!"
                )

            else:
                print(
                    f"Reading {output} through {input} yielded {readback} as expected."
                )

    def verify(self):
        self.build_and_program()
        self.verify_output_probe_initial_values()
        self.verify_probes_update()


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_output_probe_initial_values_xilinx():
    IOCoreLoopbackTest(Nexys4DDRPlatform(), "/dev/ttyUSB1").verify()


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_output_probe_initial_values_ice40():
    IOCoreLoopbackTest(ICEStickPlatform(), "/dev/ttyUSB2").verify()
