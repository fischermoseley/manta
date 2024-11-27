import os
from random import getrandbits

import pytest
from amaranth import *
from amaranth.lib import io
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from manta import *
from manta.utils import *


class MemoryCoreLoopbackTest(Elaboratable):
    def __init__(self, platform, mode, width, depth, port):
        self.platform = platform
        self.mode = mode
        self.width = width
        self.depth = depth
        self.port = port

    def elaborate(self, platform):
        # Since we know that all the tests will be called only after the FPGA
        # is programmed, we can just push all the wiring into the elaborate
        # method, instead of needing to define Manta in the __init__() method

        user_addr = Signal(range(self.depth))
        user_data_in = Signal(self.width)
        user_data_out = Signal(self.width)
        user_write_enable = Signal()

        self.manta = manta = Manta()
        manta.cores.mem = MemoryCore(self.mode, self.width, self.depth)
        manta.cores.io = IOCore(
            inputs=[user_data_out], outputs=[user_addr, user_data_in, user_write_enable]
        )
        manta.interface = UARTInterface(
            port=self.port, baudrate=3e6, clock_freq=platform.default_clk_frequency
        )

        m = Module()
        m.submodules.manta = self.manta

        uart_pins = platform.request("uart", dir={"tx": "-", "rx": "-"})
        m.submodules.uart_rx = uart_rx = io.Buffer("i", uart_pins.rx)
        m.submodules.uart_tx = uart_tx = io.Buffer("o", uart_pins.tx)

        m.d.comb += self.manta.interface.rx.eq(uart_rx.i)
        m.d.comb += uart_tx.o.eq(self.manta.interface.tx)

        m.d.comb += self.manta.cores.mem.user_addr.eq(user_addr)

        if self.mode in ["bidirectional", "fpga_to_host"]:
            m.d.comb += self.manta.cores.mem.user_data_in.eq(user_data_in)
            m.d.comb += self.manta.cores.mem.user_write_enable.eq(user_write_enable)

        if self.mode in ["bidirectional", "host_to_fpga"]:
            m.d.comb += user_data_out.eq(self.manta.cores.mem.user_data_out)

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def write_user_side(self, addr, data):
        self.manta.cores.io.set_probe("user_write_enable", 0)
        self.manta.cores.io.set_probe("user_addr", addr)
        self.manta.cores.io.set_probe("user_data_in", data)
        self.manta.cores.io.set_probe("user_write_enable", 1)
        self.manta.cores.io.set_probe("user_write_enable", 0)

    def read_user_side(self, addr):
        self.manta.cores.io.set_probe("user_write_enable", 0)
        self.manta.cores.io.set_probe("user_addr", addr)
        return self.manta.cores.io.get_probe("user_data_out")

    def verify(self):
        self.build_and_program()

        if self.mode in ["bidirectional", "host_to_fpga"]:
            for addr in jumble(range(self.depth)):
                # Write a random value to a random bus address
                data = getrandbits(self.width)
                self.manta.cores.mem.write(addr, data)

                # Verify the same number is returned when reading on the user side
                readback = self.read_user_side(addr)
                if readback != data:
                    raise ValueError(
                        f"Memory read from {hex(addr)} returned {hex(readback)} instead of {hex(data)}."
                    )

        if self.mode in ["bidirectional", "fpga_to_host"]:
            for addr in jumble(range(self.depth)):
                # Write a random value to a random user address
                data = getrandbits(self.width)
                self.write_user_side(addr, data)

                # Verify the same number is returned when reading on the bus side
                readback = self.manta.cores.mem.read(addr)
                if readback != data:
                    raise ValueError(
                        f"Memory read from {hex(addr)} returned {hex(readback)} instead of {hex(data)}."
                    )


# Nexys4DDR Tests
modes = ["fpga_to_host", "host_to_fpga", "bidirectional"]
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
