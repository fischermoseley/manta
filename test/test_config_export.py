import tempfile

import yaml
from amaranth import *

from manta import *


def test_io_core_dump():
    # Create some dummy signals to pass to the IO Core
    probe0 = Signal(1)
    probe1 = Signal(2)
    probe2 = Signal(3)
    probe3 = Signal(4, init=13)

    # Create Manta instance
    manta = Manta()
    manta.cores.test_core = IOCore(inputs=[probe0, probe1], outputs=[probe2, probe3])

    # Create Temporary File
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    # Export Manta configuration
    manta.export_config(tf.name)

    # Parse the exported YAML
    with open(tf.name, "r") as f:
        data = yaml.safe_load(f)

    # Verify that exported YAML matches configuration
    expected = {
        "cores": {
            "test_core": {
                "type": "io",
                "inputs": {"probe0": 1, "probe1": 2},
                "outputs": {
                    "probe2": {"width": 3, "initial_value": 0},
                    "probe3": {"width": 4, "initial_value": 13},
                },
            }
        }
    }

    if data != expected:
        raise ValueError("Exported YAML does not match configuration!")


def test_memory_core_dump():
    # Create Manta instance
    manta = Manta()
    manta.cores.test_core = MemoryCore(
        mode="bidirectional",
        width=32,
        depth=1024,
    )

    # Create Temporary File
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    # Export Manta configuration
    manta.export_config(tf.name)

    # Parse the exported YAML
    with open(tf.name, "r") as f:
        data = yaml.safe_load(f)

    # Verify that exported YAML matches configuration
    expected = {
        "cores": {
            "test_core": {
                "type": "memory",
                "mode": "bidirectional",
                "width": 32,
                "depth": 1024,
            }
        }
    }

    if data != expected:
        raise ValueError("Exported YAML does not match configuration!")


def test_logic_analyzer_core_dump():
    # Create some dummy signals to pass to the Logic Analyzer
    probe0 = Signal(1)
    probe1 = Signal(2)
    probe2 = Signal(3)

    # Create Manta instance
    manta = Manta()
    manta.cores.test_core = LogicAnalyzerCore(
        sample_depth=2048, probes=[probe0, probe1, probe2]
    )

    # Create Temporary File
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    # Export Manta configuration
    manta.export_config(tf.name)

    # Parse the exported YAML
    with open(tf.name, "r") as f:
        data = yaml.safe_load(f)

    # Verify that exported YAML matches configuration
    expected = {
        "cores": {
            "test_core": {
                "type": "logic_analyzer",
                "sample_depth": 2048,
                "probes": {"probe0": 1, "probe1": 2, "probe2": 3},
            }
        }
    }

    if data != expected:
        raise ValueError("Exported YAML does not match configuration!")


def test_uart_interface_dump():
    manta = Manta()
    manta.interface = UARTInterface(
        port="/dev/ttyUSB0", baudrate=115200, clock_freq=100e6
    )

    # Create Temporary File
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    # Export Manta configuration
    manta.export_config(tf.name)

    # Parse the exported YAML
    with open(tf.name, "r") as f:
        data = yaml.safe_load(f)

    # Verify that exported YAML matches configuration
    expected = {
        "uart": {
            "port": "/dev/ttyUSB0",
            "baudrate": 115200,
            # Be careful with the float comparison here, copy-pasting from the
            # exported YAML seems to have the best results. Otherwise this test
            # will fail when it shouldn't.
            "clock_freq": 100000000.0,
            "chunk_size": 256,
            "stall_interval": 16,
        }
    }

    if data != expected:
        raise ValueError("Exported YAML does not match configuration!")


def test_ethernet_interface_dump():
    manta = Manta()
    manta.interface = EthernetInterface(
        fpga_ip_addr="192.168.0.101",
        host_ip_addr="192.168.0.100",
        udp_port=2000,
        phy="LiteEthPHYRMII",
        clk_freq=50e6,
        refclk_freq=50e6,
        vendor="xilinx",
        toolchain="vivado",
    )

    # Create Temporary File
    tf = tempfile.NamedTemporaryFile(delete=False)
    tf.close()

    # Export Manta configuration
    manta.export_config(tf.name)

    # Parse the exported YAML
    with open(tf.name, "r") as f:
        data = yaml.safe_load(f)

    # Verify that exported YAML matches configuration
    expected = {
        "ethernet": {
            "phy": "LiteEthPHYRMII",
            "vendor": "xilinx",
            "toolchain": "vivado",
            # Be careful with the float comparison here, copy-pasting from the
            # exported YAML seems to have the best results. Otherwise this test
            # will fail when it shouldn't.
            "clk_freq": 50000000.0,
            "refclk_freq": 50000000.0,
            "fpga_ip_addr": "192.168.0.101",
            "host_ip_addr": "192.168.0.100",
            "udp_port": 2000,
        }
    }

    if data != expected:
        raise ValueError("Exported YAML does not match configuration!")
