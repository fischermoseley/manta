import os
from random import getrandbits

import pytest
from amaranth import *
from amaranth.lib import io
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from manta import *
from manta.utils import *


class UARTBaudrateMismatchTest(Elaboratable):
    def __init__(self, platform, port, baudrate, percent_slowdown, stall_interval):
        self.platform = platform
        self.port = port
        self.baudrate = baudrate
        self.slowed_baudrate = baudrate * (1 - (percent_slowdown / 100))
        self.stall_interval = stall_interval

    def elaborate(self, platform):
        # Since we know that all the tests will be called only after the FPGA
        # is programmed, we can just push all the wiring into the elaborate
        # method, instead of needing to define Manta in the __init__() method

        self.manta = manta = Manta()
        manta.cores.mem = MemoryCore(
            "bidirectional",
            width=16,
            depth=1024,
        )

        # Set the RTL to a slower baudrate. Later, we'll manually set the
        # UARTInterface's _baudrate attribute back to the non-slowed baudrate
        manta.interface = UARTInterface(
            port=self.port,
            baudrate=self.slowed_baudrate,
            clock_freq=platform.default_clk_frequency,
            stall_interval=self.stall_interval,
        )

        m = Module()
        m.submodules.manta = self.manta

        uart_pins = platform.request("uart", dir={"tx": "-", "rx": "-"})
        m.submodules.uart_rx = uart_rx = io.Buffer("i", uart_pins.rx)
        m.submodules.uart_tx = uart_tx = io.Buffer("o", uart_pins.tx)

        m.d.comb += self.manta.interface.rx.eq(uart_rx.i)
        m.d.comb += uart_tx.o.eq(self.manta.interface.tx)

        return m

    def build_and_program(self):
        self.platform.build(self, do_program=True)

    def fill_memory(self):
        self.addrs = list(range(1024))
        self.datas = [getrandbits(16) for _ in self.addrs]
        self.manta.cores.mem.write(self.addrs, self.datas)

    def verify_memory(self, batches):
        datas = self.manta.cores.mem.read(self.addrs * batches)
        if datas != (self.datas * batches):
            raise ValueError("Data written does not match data read back!")

    def verify(self):
        self.build_and_program()

        # Set the class back to the normal baudrate, which will be used when
        # the port is opened
        self.manta.interface._baudrate = self.baudrate

        # Write a bunch of data
        self.fill_memory()

        # Read it back a few times, see if it's good
        self.verify_memory(10)


# Nexys4DDR Tests
nexys4ddr_pass_cases = [
    (3e6, 0, 1024),  # No clock mismatch, with no mitigation
    (3e6, 0, 16),  # No clock mismatch, with mitigation
    (3e6, 1, 16),  # Light clock mismatch, with light mitigation
    (3e6, 2, 7),  # Heavy clock mismatch, with heavy mitigation
]


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize(
    "baudrate, percent_slowdown, stall_interval", nexys4ddr_pass_cases
)
def test_baudrate_mismatch_xilinx_passes(baudrate, percent_slowdown, stall_interval):
    UARTBaudrateMismatchTest(
        platform=Nexys4DDRPlatform(),
        port=os.environ["NEXYS4DDR_PORT"],
        baudrate=baudrate,
        percent_slowdown=percent_slowdown,
        stall_interval=stall_interval,
    ).verify()


nexys4ddr_fail_cases = [
    (3e6, 2, 1024),  # Heavy clock mismatch, no mitigation
    (3e6, 2, 16),  # Heavy clock mismatch, light mitigation
]


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize(
    "baudrate, percent_slowdown, stall_interval", nexys4ddr_fail_cases
)
def test_baudrate_mismatch_xilinx_fails(baudrate, percent_slowdown, stall_interval):
    with pytest.raises(ValueError, match="Only got"):
        UARTBaudrateMismatchTest(
            platform=Nexys4DDRPlatform(),
            port=os.environ["NEXYS4DDR_PORT"],
            baudrate=baudrate,
            percent_slowdown=percent_slowdown,
            stall_interval=stall_interval,
        ).verify()


# IceStick Tests
ice40_pass_cases = [
    (115200, 0, 1024),  # No clock mismatch, with no mitigation
    (115200, 0, 16),  # No clock mismatch, with mitigation
    (115200, 1, 16),  # Light clock mismatch, with light mitigation
    (115200, 2, 7),  # Heavy clock mismatch, with heavy mitigation
]


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize("baudrate, percent_slowdown, stall_interval", ice40_pass_cases)
def test_baudrate_mismatch_ice40_passes(baudrate, percent_slowdown, stall_interval):
    UARTBaudrateMismatchTest(
        platform=ICEStickPlatform(),
        port=os.environ["ICESTICK_PORT"],
        baudrate=baudrate,
        percent_slowdown=percent_slowdown,
        stall_interval=stall_interval,
    ).verify()


ice40_fail_cases = [
    (115200, 1, 1024),  # Light clock mismatch, no mitigation
    (115200, 2, 1024),  # Heavy clock mismatch, no mitigation
    (115200, 2, 16),  # Heavy clock mismatch, light mitigation
]


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
@pytest.mark.parametrize("baudrate, percent_slowdown, stall_interval", ice40_fail_cases)
def test_baudrate_mismatch_ice40_fails(baudrate, percent_slowdown, stall_interval):
    with pytest.raises(ValueError, match="Only got"):
        UARTBaudrateMismatchTest(
            platform=ICEStickPlatform(),
            port=os.environ["ICESTICK_PORT"],
            baudrate=baudrate,
            percent_slowdown=percent_slowdown,
            stall_interval=stall_interval,
        ).verify()
