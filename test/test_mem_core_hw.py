from amaranth import *
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform
from amaranth_boards.icestick import ICEStickPlatform
from manta import Manta
from manta.utils import *
import pytest
from random import randint, sample
from math import ceil, log2

"""
Fundamentally we want a function to generate a configuration (as a dictionary)
for a memory core given the width, depth, and platform. This could be a random
configuration, or a standard one.
"""


class MemoryCoreLoopbackTest(wiring.Component):
    def __init__(self, platform, width, depth, port):
        self.platform = platform
        self.width = width
        self.depth = depth
        self.port = port

        self.config = self.platform_specific_config()
        self.manta = Manta(self.config)

    def platform_specific_config(self):
        return {
            "cores": {
                "mem_core": {
                    "type": "memory",
                    "mode": "fpga_to_host",
                    "width": self.width,
                    "depth": self.depth,
                },
                "io_core": {
                    "type": "io",
                    "outputs": {
                        "addr": ceil(log2(self.depth)),
                        "data": self.width,
                        "we": 1,
                    },
                },
            },
            "uart": {
                "port": self.port,
                "baudrate": 3e6,
                "clock_freq": self.platform.default_clk_frequency,
            },
        }

    def get_probe(self, name):
        # This is a hack! And should be removed once the full Amaranth-native
        # API is built out
        for i in self.manta.io_core._inputs:
            if i.name == name:
                return i

        for o in self.manta.io_core._outputs:
            if o.name == name:
                return o

        return None

    def elaborate(self, platform):
        m = Module()
        m.submodules.manta = self.manta

        uart_pins = platform.request("uart")

        addr = self.get_probe("addr")
        data = self.get_probe("data")
        we = self.get_probe("we")

        m.d.comb += [
            self.manta.mem_core.user_addr.eq(addr),
            self.manta.mem_core.user_data_in.eq(data),
            self.manta.mem_core.user_write_enable.eq(we),
            self.manta.interface.rx.eq(uart_pins.rx.i),
            uart_pins.tx.o.eq(self.manta.interface.tx),
        ]

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def write_user_side(self, addr, data):
        self.manta.io_core.set_probe("we", 0)
        self.manta.io_core.set_probe("addr", addr)
        self.manta.io_core.set_probe("data", data)
        self.manta.io_core.set_probe("we", 1)
        self.manta.io_core.set_probe("we", 0)

    def verify_register(self, addr, expected_data):
        data = self.manta.mem_core.read(addr)

        if data != expected_data:
            raise ValueError(
                f"Memory read from {hex(addr)} returned {hex(data)} instead of {hex(expected_data)}."
            )

    def verify(self):
        self.build_and_program()

        # Read and write randomly from the bus side
        for addr in jumble(range(self.depth)):
            data = randint(0, 2**self.width - 1)
            self.write_user_side(addr, data)
            self.verify_register(addr, data)


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_mem_core_xilinx():
    port = "/dev/serial/by-id/usb-Digilent_Digilent_USB_Device_210292696307-if01-port0"
    MemoryCoreLoopbackTest(Nexys4DDRPlatform(), 33, 1024, port).verify()


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_mem_core_ice40():
    port = "/dev/serial/by-id/usb-Lattice_Lattice_FTUSB_Interface_Cable-if01-port0"
    MemoryCoreLoopbackTest(ICEStickPlatform(), 1, 2, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 1, 512, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 1, 1024, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 8, 2, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 8, 512, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 8, 1024, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 14, 512, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 14, 1024, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 16, 512, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 16, 1024, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 33, 512, port).verify()
    MemoryCoreLoopbackTest(ICEStickPlatform(), 33, 1024, port).verify()
