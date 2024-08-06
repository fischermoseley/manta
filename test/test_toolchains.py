import pytest
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform
from amaranth_boards.test.blinky import *
from manta.utils import *


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_nexys4_ddr_tools():
    Nexys4DDRPlatform().build(Blinky(), do_program=False)


@pytest.mark.skipif(not ice40_tools_installed(), reason="no toolchain installed")
def test_ice40_tools():
    ICEStickPlatform().build(Blinky(), do_program=False)
