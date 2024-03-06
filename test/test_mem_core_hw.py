from amaranth import *
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform
from amaranth_boards.icestick import ICEStickPlatform
from manta import Manta
from manta.utils import *
import pytest
from random import getrandbits
from math import ceil, log2
import os


class MemoryCoreLoopbackTest(Elaboratable):
    def __init__(self, platform, mode, width, depth, port):
        self.platform = platform
        self.mode = mode
        self.width = width
        self.depth = depth
        self.port = port

        self.config = self.platform_specific_config()
        self.manta = Manta(self.config)

    def platform_specific_config(self):
        return {
            "cores": {
                "io_core": {
                    "type": "io",
                    "outputs": {
                        "user_addr": ceil(log2(self.depth)),
                        "user_data_in": self.width,
                        "user_write_enable": 1,
                    },
                    "inputs": {
                        "user_data_out": self.width,
                    },
                },
                "mem_core": {
                    "type": "memory",
                    "mode": self.mode,
                    "width": self.width,
                    "depth": self.depth,
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

        user_addr = self.get_probe("user_addr")
        user_data_in = self.get_probe("user_data_in")
        user_data_out = self.get_probe("user_data_out")
        user_write_enable = self.get_probe("user_write_enable")

        m.d.comb += self.manta.interface.rx.eq(uart_pins.rx.i)
        m.d.comb += uart_pins.tx.o.eq(self.manta.interface.tx)
        m.d.comb += self.manta.mem_core.user_addr.eq(user_addr)

        if self.mode in ["bidirectional", "fpga_to_host"]:
            m.d.comb += self.manta.mem_core.user_data_in.eq(user_data_in)
            m.d.comb += self.manta.mem_core.user_write_enable.eq(user_write_enable)

        if self.mode in ["bidirectional", "host_to_fpga"]:
            m.d.comb += user_data_out.eq(self.manta.mem_core.user_data_out)

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def write_user_side(self, addr, data):
        self.manta.io_core.set_probe("user_write_enable", 0)
        self.manta.io_core.set_probe("user_addr", addr)
        self.manta.io_core.set_probe("user_data_in", data)
        self.manta.io_core.set_probe("user_write_enable", 1)
        self.manta.io_core.set_probe("user_write_enable", 0)

    def read_user_side(self, addr):
        self.manta.io_core.set_probe("user_write_enable", 0)
        self.manta.io_core.set_probe("user_addr", addr)
        return self.manta.io_core.get_probe("user_data_out")

    def verify(self):
        self.build_and_program()

        if self.mode in ["bidirectional", "host_to_fpga"]:
            for addr in jumble(range(self.depth)):

                # Write a random balue to a random bus address
                data = getrandbits(self.width)
                self.manta.mem_core.write(addr, data)

                # Verify the same number is returned when reading on the user side
                readback = self.read_user_side(addr)
                if readback != data:
                    raise ValueError(
                        f"Memory read from {hex(addr)} returned {hex(data)} instead of {hex(readback)}."
                    )

        if self.mode in ["bidirectional", "fpga_to_host"]:
            for addr in jumble(range(self.depth)):

                # Write a random value to a random user address
                data = getrandbits(self.width)
                self.write_user_side(addr, data)

                # Verify the same number is returned when reading on the bus side
                readback = self.manta.mem_core.read(addr)
                if readback != data:
                    raise ValueError(
                        f"Memory read from {hex(addr)} returned {hex(data)} instead of {hex(readback)}."
                    )


# Nexys4DDR Tests

# Omit the bidirectional mode for now, pending completion of:
# https://github.com/amaranth-lang/amaranth/issues/1011
modes = ["fpga_to_host", "host_to_fpga"]
widths = [1, 8, 14, 16, 33]
depths = [2, 512, 1024]
nexys4ddr_cases = [(m, w, d) for m in modes for w in widths for d in depths]


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize("mode, width, depth", nexys4ddr_cases)
def test_mem_core_xilinx(mode, width, depth):
    port = os.environ["NEXYS4DDR_PORT"]
    MemoryCoreLoopbackTest(Nexys4DDRPlatform(), mode, width, depth, port).verify()


# IceStick Tests
modes = ["fpga_to_host", "host_to_fpga"]
widths = [1, 8, 14, 16, 33]
depths = [2, 512, 1024]
ice40_cases = [(m, w, d) for m in modes for w in widths for d in depths]


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize("mode, width, depth", ice40_cases)
def test_mem_core_ice40(mode, width, depth):
    port = os.environ["ICESTICK_PORT"]
    MemoryCoreLoopbackTest(ICEStickPlatform(), mode, width, depth, port).verify()
