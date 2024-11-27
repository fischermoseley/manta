from pathlib import Path
from time import sleep

from amaranth import *
from amaranth.lib import io

from manta import *


class EthernetIOCoreExample(Elaboratable):
    def __init__(self, platform, port):
        self.platform = platform

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

        # Autodetect the number of LEDs on the platform
        resources = platform.resources.keys()
        self.n_leds = max([i for name, i in resources if name == "led"])

        # Add IOCore to Manta instance
        self.leds = Signal(self.n_leds)
        self.manta.cores.io = IOCore(outputs=[self.leds])

    def elaborate(self, platform):
        m = Module()

        # Create 50MHz clock domain
        m.domains.ethclk = ethclk = ClockDomain()
        m.submodules.divider = Instance(
            "divider",
            ("i", "clk", ClockSignal()),
            ("o", "ethclk", ethclk.clk),
        )
        divider_sv_path = Path(__file__).parent / "../common/divider.sv"
        platform.add_file("divider.sv", open(divider_sv_path))

        # Add Manta as a submodule
        m.submodules.manta = DomainRenamer("ethclk")(self.manta)

        # Wire each LED to Manta's IO Core output
        for i in range(self.n_leds):
            led = io.Buffer("o", platform.request("led", i, dir="-"))
            m.d.comb += led.o.eq(self.leds[i])
            m.submodules += led

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

    def test(self):
        # Build and program the FPGA
        self.platform.build(self, do_program=True)

        # Iterate through all the LEDs, blinking them off and on
        i = 0
        while True:
            self.manta.cores.io.set_probe("leds", 1 << i)
            i = (i + 1) % self.n_leds
            sleep(0.1)


# Although Amaranth provides an environment that is almost entirely independent
# of FPGA vendor or family, it does not provide any facilities for clock
# generation. As a result, this example design includes an external Verilog
# snippet containing a clock generator created by Vivado's Clock Wizard.
# This uses a MMCM clock generation primitive to make a 50MHz clock from the
# onboard 100MHz oscillator, in order to drive the Ethernet PHY. This primitive
# is only available on Xilinx Series-7 parts, so this example will only work on
# Series-7 parts clocked at 100MHz that have RMII PHYs connected...which is
# pretty much just the Nexys4DDR and the Arty A7 :)

if __name__ == "__main__":
    from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

    EthernetIOCoreExample(platform=Nexys4DDRPlatform(), port="auto").test()
