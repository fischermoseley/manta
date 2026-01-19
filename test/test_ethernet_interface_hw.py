import time
from random import getrandbits

import pytest
from amaranth import *
from amaranth.lib import io
from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

from manta import *
from manta.utils import *


class EthernetMemoryCoreTest(Elaboratable):
    def __init__(self, platform):
        self.platform = platform
        self.width = 28
        self.depth = 612

        # Create Manta instance
        self.manta = Manta()

        # Configure it to communicate over Ethernet
        self.manta.interface = EthernetInterface(
            phy="LiteEthPHYRMII",
            device="xc7a",
            vendor="xilinx",
            toolchain="vivado",
            refclk_freq=50e6,
            clk_freq=50e6,
            fpga_ip_addr="10.0.0.2",
            host_ip_addr="10.0.0.1",
            udp_port=2000,
        )

        self.manta.cores.mem = MemoryCore("bidirectional", self.width, self.depth)

    def elaborate(self, platform):
        m = Module()

        # Create 50MHz clock domain
        m.domains.ethclk = ethclk = ClockDomain()
        m.submodules.divider = Instance(
            "divider",
            ("i", "clk", ClockSignal()),
            ("o", "ethclk", ethclk.clk),
        )
        platform.add_file("divider.sv", open("examples/common/divider.sv"))

        # Add Manta as a submodule
        m.submodules.manta = DomainRenamer("ethclk")(self.manta)

        # This is only required for Amaranth < 0.5.2
        eth_pin_names = [
            "mdio",
            "mdc",
            "reset",
            "rxd",
            "rxerr",
            "txd",
            "txen",
            "crs_dv",
            "int",
            "clk",
        ]
        eth_pin_dirs = {name: "-" for name in eth_pin_names}
        eth_pins = platform.request("eth", dir=eth_pin_dirs)

        # For Amaranth > 0.5.2, this simpler syntax may be used:
        # eth_pins = platform.request("eth")

        # Run the PHY's ethclk from the 50MHz divider
        m.submodules.eth_clk_io_buf = eth_clk_io_buf = io.Buffer("o", eth_pins.clk)
        m.d.comb += eth_clk_io_buf.o.eq(ethclk.clk)

        # Wire Ethernet pins to the Manta instance
        self.manta.interface.set_rmii_phy_io(
            rmii_clocks_ref_clk=ethclk.clk,
            rmii_rst_n=eth_pins.reset.io,
            rmii_rx_data=eth_pins.rxd.io,
            rmii_crs_dv=eth_pins.crs_dv.io,
            rmii_tx_en=eth_pins.txen.io,
            rmii_tx_data=eth_pins.txd.io,
            rmii_mdc=eth_pins.mdc.io,
            rmii_mdio=eth_pins.mdio.io,
        )

        return m

    def verify(self):
        self.platform.build(self, do_program=True)

        # Wait for the FPGA to acquire IP address
        time.sleep(5)

        for addr in jumble(range(self.depth)):
            data = getrandbits(self.width)
            self.manta.cores.mem.write(addr, data)

            # Verify the same number is returned when reading
            readback = self.manta.cores.mem.read(addr)
            if readback != data:
                raise ValueError(
                    f"Memory read from {hex(addr)} returned {hex(readback)} instead of {hex(data)}"
                )


@pytest.mark.skipif(not xilinx_tools_installed(), reason="no toolchain installed")
def test_mem_core_xilinx():
    EthernetMemoryCoreTest(Nexys4DDRPlatform()).verify()
