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


class MemoryCoreLoopbackTest(Elaboratable):
    def __init__(self, platform, width, depth, port):
        self.platform = platform
        self.width = width
        self.depth = depth
        self.port = port

        self.config = self.platform_specific_config()
        self.m = Manta(self.config)

    def platform_specific_config(self):
        return {
            "cores": {
                "mem_core": {
                    "type": "memory_read_only",
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

    def elaborate(self, platform):
        m = Module()
        m.submodules["manta"] = self.m

        uart_pins = platform.request("uart")

        m.d.comb += [
            self.m.mem_core.user_addr.eq(self.m.io_core.addr),
            self.m.mem_core.user_data.eq(self.m.io_core.data),
            self.m.mem_core.user_we.eq(self.m.io_core.we),
            self.m.interface.rx.eq(uart_pins.rx.i),
            uart_pins.tx.o.eq(self.m.interface.tx),
        ]

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def write_user_side(self, addr, data):
        self.m.io_core.set_probe("we", 0)
        self.m.io_core.set_probe("addr", addr)
        self.m.io_core.set_probe("data", data)
        self.m.io_core.set_probe("we", 1)
        self.m.io_core.set_probe("we", 0)

    def verify_register(self, addr, expected_data):
        data = self.m.mem_core.read_from_user_addr(addr)

        if data != expected_data:
            raise ValueError(
                f"Memory read from {hex(addr)} returned {hex(data)} instead of {hex(expected_data)}."
            )

    def verify(self):
        self.build_and_program()

        # Read and write randomly from the bus side
        for addr in sample(range(self.depth), k=self.depth):
            data = randint(0, 2**self.width - 1)
            self.write_user_side(addr, data)
            self.verify_register(addr, data)


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_mem_core_xilinx():
    MemoryCoreLoopbackTest(Nexys4DDRPlatform(), 33, 1024, "/dev/ttyUSB1").verify()


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_mem_core_ice40():
    port = "/dev/ttyUSB2"
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
