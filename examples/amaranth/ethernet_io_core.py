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
            clk_freq = 50e6,
            fpga_ip_addr = "10.0.0.2",
            host_ip_addr = "10.0.0.1",
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
        platform.add_file("divider.sv", open("divider.sv"))

        # Add Manta as a submodule
        m.submodules.manta = DomainRenamer("ethclk")(self.manta)

        # Wire each LED to Manta's IO Core output
        for i in range(self.n_leds):
            led = io.Buffer("o", platform.request("led", i, dir="-"))
            m.d.comb += led.o.eq(self.leds[i])
            m.submodules += led

        # Wire Ethernet pins to the Manta instance

        # This is only required for Amaranth < 0.5.2
        eth_pin_names = ["mdio", "mdc", "reset", "rxd", "rxerr", "txd", "txen", "crs_dv", "int", "clk"]
        eth_pin_dirs = {name: "-" for name in eth_pin_names}
        eth_pins = platform.request("eth", dir=eth_pin_dirs)

        # For Amaranth > 0.5.2, this simpler syntax may be used:
        # eth_pins = platform.request("eth")

        # self.manta.interface.set_phy_io(
        #     rmii_clocks_ref_clk = eth_pins.clk,
        #     rmii_rst_n = eth_pins.reset,
        #     rmii_rx_data = eth_pins.rxd,
        #     rmii_crs_dv = eth_pins.crs_dv,
        #     rmii_tx_en = eth_pins.txen,
        #     rmii_tx_data = eth_pins.txd,
        #     rmii_mdc = eth_pins.mdc,
        #     rmii_mdio = eth_pins.mdio,
        # )

        m.submodules.eth_clk_io_buf = eth_clk_io_buf = io.Buffer("o", eth_pins.clk)
        m.d.comb += eth_clk_io_buf.o.eq(ethclk.clk)

        self.manta.interface._phy_io = [
            ("i", "rmii_clocks_ref_clk", ethclk.clk),
            ("o", "rmii_rst_n", eth_pins.reset.io),
            ("i", "rmii_rx_data", eth_pins.rxd.io),
            ("i", "rmii_crs_dv", eth_pins.crs_dv.io),
            ("o", "rmii_tx_en", eth_pins.txen.io),
            ("o", "rmii_tx_data", eth_pins.txd.io),
            ("o", "rmii_mdc", eth_pins.mdc.io),
            ("io", "rmii_mdio", eth_pins.mdio.io),
        ]

        return m

    def test(self):
        # Build and program the FPGA
        # self.platform.build(self, do_program=True)

        # Iterate through all the LEDs, blinking them off and on
        i = 0
        while True:
            self.manta.cores.io.set_probe("leds", 1 << i)
            i = (i + 1) % self.n_leds
            sleep(0.1)


# Amaranth has a built-in build system, and well as a set of platform
# definitions for a huge number of FPGA boards. The class defined above is
# very generic, as it specifies a design independent of any particular FGPA
# board. This means that by changing which platform you pass UARTIOCoreExample
# below, you can port this example to any FPGA board!

if __name__ == "__main__":
    from amaranth_boards.nexys4ddr import Nexys4DDRPlatform

    EthernetIOCoreExample(platform=Nexys4DDRPlatform(), port="auto").test()
