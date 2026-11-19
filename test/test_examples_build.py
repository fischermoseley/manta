import os
import subprocess
import sys

import pytest
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from test.utils import check_tools

verilog_root_dirs = [
    ("examples/verilog/icestick/uart_io_core", ICEStickPlatform()),
    ("examples/verilog/icestick/uart_logic_analyzer", ICEStickPlatform()),
    ("examples/verilog/nexys4_ddr/ether_logic_analyzer_io_core", Nexys4DDRPlatform()),
    ("examples/verilog/nexys4_ddr/uart_host_to_fpga_mem", Nexys4DDRPlatform()),
    ("examples/verilog/nexys4_ddr/uart_io_core", Nexys4DDRPlatform()),
    ("examples/verilog/nexys4_ddr/uart_logic_analyzer", Nexys4DDRPlatform()),
]


@pytest.mark.parametrize("root_dir, platform", verilog_root_dirs)
def test_verilog_examples_build(root_dir, platform):
    check_tools(platform, need_prog_tool=False, need_port=False)
    subprocess.run(["./build.sh"], cwd=root_dir, capture_output=True, text=True, check=True)


# Patch the PATH variable so imports from examples/ are possible
# ruff: disable[E402]
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

# Import Platforms
from amaranth_boards.icestick import ICEStickPlatform
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

# Import Examples
from examples.amaranth.ethernet_io_core import EthernetIOCoreExample
from examples.amaranth.uart_io_core import UARTIOCoreExample
from examples.amaranth.uart_logic_analyzer import UARTLogicAnalyzerExample
from examples.amaranth.uart_memory_core import UARTMemoryCoreExample

# ruff: enable[E402]

# Manually specify a list of examples/platforms to test.

# This is necessary as some examples don't work without some amount of onboard
# IO - for instance, the UARTMemoryCore example requires switches and LEDs to
# read out the memory provided by Manta, but the Icestick doesn't have any
# switches.
amaranth_examples_cases = [
    (UARTIOCoreExample, ICEStickPlatform()),
    (UARTIOCoreExample, Nexys4DDRPlatform()),
    (UARTLogicAnalyzerExample, ICEStickPlatform()),
    (UARTLogicAnalyzerExample, Nexys4DDRPlatform()),
    (UARTMemoryCoreExample, Nexys4DDRPlatform()),
    (EthernetIOCoreExample, Nexys4DDRPlatform()),
]


@pytest.mark.parametrize("example, platform", amaranth_examples_cases)
def test_amaranth_examples_build(example, platform):
    check_tools(platform, need_prog_tool=False, need_port=False)

    design = example(platform, port="auto")
    design.platform.build(design, do_program=False)
