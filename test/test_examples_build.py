import os
import subprocess
import sys

import pytest

verilog_root_dirs = [
    "examples/verilog/icestick/uart_io_core",
    "examples/verilog/icestick/uart_logic_analyzer",
    "examples/verilog/nexys4_ddr/ether_logic_analyzer_io_core",
    "examples/verilog/nexys4_ddr/uart_host_to_fpga_mem",
    "examples/verilog/nexys4_ddr/uart_io_core",
    "examples/verilog/nexys4_ddr/uart_logic_analyzer",
]


@pytest.mark.parametrize("root_dir", verilog_root_dirs)
def test_verilog_examples_build(root_dir):
    result = subprocess.run(
        ["./build.sh"], cwd=root_dir, capture_output=True, text=True
    )

    if result.returncode != 0:
        raise ValueError(f"Command failed with return code {result.returncode}.")


# Patch the PATH variable so imports from examples/ are possible
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

# Manually specify a list of examples/platforms to test.

# This is necessary as some examples don't work without some amount of onboard
# IO - for instance, the UARTMemoryCore example requires switches and LEDs to
# read out the memory provided by Manta, but the Icestick doesn't have any
# switches.
amaranth_examples_cases = [
    (UARTIOCoreExample, ICEStickPlatform),
    (UARTIOCoreExample, Nexys4DDRPlatform),
    (UARTLogicAnalyzerExample, ICEStickPlatform),
    (UARTLogicAnalyzerExample, Nexys4DDRPlatform),
    (UARTMemoryCoreExample, Nexys4DDRPlatform),
    (EthernetIOCoreExample, Nexys4DDRPlatform),
]


@pytest.mark.parametrize("example, platform", amaranth_examples_cases)
def test_amaranth_examples_build(example, platform):
    design = example(platform(), port="auto")
    design.platform.build(design, do_program=False)
