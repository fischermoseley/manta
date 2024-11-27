import socket
from random import getrandbits

from amaranth import *
from amaranth.hdl import IOPort

from manta.ethernet.sink_bridge import UDPSinkBridge
from manta.ethernet.source_bridge import UDPSourceBridge
from manta.utils import *


class EthernetInterface(Elaboratable):
    """
    A synthesizable module for Ethernet (UDP) communication between a host
    machine and the FPGA.
    """

    def __init__(
        self, phy, clk_freq, fpga_ip_addr, host_ip_addr, udp_port=2001, **kwargs
    ):
        """
        This function is the main mechanism for configuring an Ethernet
        Interface in an Amaranth-native design.

        Args:
            phy (str): The name of the LiteEth PHY class to use. Select the
                appropriate one from [this list](https://github.com/enjoy-digital/liteeth/blob/main/liteeth/phy/__init__.py#L25-L45)
                for your FPGA vendor and family.

            clk_freq (int | float): The frequency of the clock provided to the
                Manta module on the FPGA, in Hertz (Hz).

            fpga_ip_addr (str): The IP address the FPGA will attempt to claim.
                Upon power-on, the FPGA will issue a DHCP request for this IP
                address. Ping this address after power-on to check if this
                request was successful, or check your router for a list of
                connected devices.

            host_ip_addr (str): The IP address of the host machine, which the
                FPGA will send packets back to.

            udp_port (Optional[int]): The UDP port to communicate over.

            **kwargs: Any additional keyword arguments to this function will
                be passed to the LiteEth RTL generator. Some examples are
                provided below:

                - mac_address (int): A 48-bit integer representing the MAC
                    address the FPGA will assume. If not provided, an address
                    within the [Locally Administered, Administratively Assigned group](https://en.wikipedia.org/wiki/MAC_address#Ranges_of_group_and_locally_administered_addresses)
                    will be randomly generated.

                - vendor (str): The vendor of your FPGA. Currently only values
                    of `xilinx` and `lattice` are supported. This is used to
                    generate (currently unused) timing constraints files.

                - toolchain (str): The toolchain being used. Currently only
                    values of `vivado` and `diamond` are supported.

                - refclk_freq (int | float): The frequency of the reference
                    clock to be provided to the Ethernet PHY, in Hertz (Hz).
                    This frequency must match the MII variant used by the PHY,
                    and speed it is being operated at. For instance, a RGMII
                    PHY may be operated at either 125MHz in Gigabit mode, or
                    25MHz in 100Mbps mode.
        """

        self._fpga_ip_addr = fpga_ip_addr
        self._host_ip_addr = host_ip_addr
        self._udp_port = udp_port
        self._phy = phy
        self._clk_freq = float(clk_freq)
        self._additional_config = kwargs
        self._check_config()

        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        # Define PHY IO, assuming that we're in a Verilog-based workflow.
        self._define_phy_io(self._phy)

        clk_freq_rounded = round(self._clk_freq)
        self._dhcp_start = Signal()
        self._dhcp_timer = Signal(range(clk_freq_rounded + 1), init=clk_freq_rounded)

        self._source_data = Signal(32)
        self._source_last = Signal()
        self._source_ready = Signal()
        self._source_valid = Signal()

        self._sink_data = Signal(32)
        self._sink_last = Signal()
        self._sink_ready = Signal()
        self._sink_valid = Signal()

    def _check_config(self):
        # Make sure UDP port is an integer in the range 0-65535
        if not isinstance(self._udp_port, int):
            raise TypeError(
                "UDP Port must be specified as an integer between 0 and 65535."
            )

        if not 0 <= self._udp_port <= 65535:
            raise ValueError("UDP Port must be between 0 and 65535.")

        # Make sure Host IP address is four bytes separated by a period
        if not isinstance(self._host_ip_addr, str):
            raise TypeError(
                "Host IP must be specified as a string in the form 'xxx.xxx.xxx.xxx'."
            )

        if len(self._host_ip_addr.split(".")) != 4:
            raise ValueError("Host IP must be specified in the form 'xxx.xxx.xxx.xxx'.")

        for byte in self._host_ip_addr.split("."):
            if not 0 <= int(byte) <= 255:
                raise ValueError(f"Invalid byte in Host IP: {byte}")

        # Make sure FPGA IP is four bytes separated by a period
        if not isinstance(self._fpga_ip_addr, str):
            raise TypeError(
                "FPGA IP must be specified as a string in the form 'xxx.xxx.xxx.xxx'."
            )

        if len(self._fpga_ip_addr.split(".")) != 4:
            raise ValueError("FPGA IP must be specified in the form 'xxx.xxx.xxx.xxx'.")

        for byte in self._fpga_ip_addr.split("."):
            if not 0 <= int(byte) <= 255:
                raise ValueError(f"Invalid byte in FPGA IP: {byte}")

    @classmethod
    def from_config(cls, config):
        return EthernetInterface(**config)

    def to_config(self):
        config = {
            "fpga_ip_addr": self._fpga_ip_addr,
            "host_ip_addr": self._host_ip_addr,
            "udp_port": self._udp_port,
            "phy": self._phy,
            "clk_freq": self._clk_freq,
        }

        return {**config, **self._additional_config}

    def get_top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """
        return [io[2] for io in self._phy_io]

    @property
    def clock_freq(self):
        return self._clk_freq

    def _binarize_ip_addr(self, ip_addr):
        octets = [bin(int(o))[2:].zfill(8) for o in ip_addr.split(".")]
        return int("".join(octets), 2)

    def _define_phy_io(self, phy):
        mii_phys = ["LiteEthPHYMII"]
        rmii_phys = ["LiteEthPHYRMII"]
        gmii_phys = ["LiteEthPHYGMII", "LiteEthPHYGMIIMII"]
        rgmii_phys = ["LiteEthS7PHYRGMII", "LiteEthECP5PHYRGMII"]
        sgmii_phys = [
            "A7_1000BASEX",
            "A7_2500BASEX",
            "K7_1000BASEX",
            "K7_2500BASEX",
            "KU_1000BASEX",
            "KU_2500BASEX",
            "USP_GTH_1000BASEX",
            "USP_GTH_2500BASEX",
            "USP_GTY_1000BASEX",
            "USP_GTY_2500BASEX",
        ]

        if phy in mii_phys:
            self.set_mii_phy_io(
                mii_clocks_rx=IOPort(name="mii_clocks_rx", width=1),
                mii_clocks_tx=IOPort(name="mii_clocks_tx", width=1),
                mii_rst_n=IOPort(name="mii_rst_n", width=1),
                mii_mdio=IOPort(name="mii_mdio", width=1),
                mii_mdc=IOPort(name="mii_mdc", width=1),
                mii_rx_dv=IOPort(name="mii_rx_dv", width=1),
                mii_rx_er=IOPort(name="mii_rx_er", width=1),
                mii_rx_data=IOPort(name="mii_rx_data", width=4),
                mii_tx_en=IOPort(name="mii_tx_en", width=1),
                mii_tx_data=IOPort(name="mii_tx_data", width=4),
                mii_col=IOPort(name="mii_col", width=1),
                mii_crs=IOPort(name="mii_crs", width=1),
            )

        elif phy in rmii_phys:
            self.set_rmii_phy_io(
                rmii_clocks_ref_clk=IOPort(name="rmii_clocks_ref_clk", width=1),
                rmii_rst_n=IOPort(name="rmii_rst_n", width=1),
                rmii_rx_data=IOPort(name="rmii_rx_data", width=2),
                rmii_crs_dv=IOPort(name="rmii_crs_dv", width=1),
                rmii_tx_en=IOPort(name="rmii_tx_en", width=1),
                rmii_tx_data=IOPort(name="rmii_tx_data", width=2),
                rmii_mdc=IOPort(name="rmii_mdc", width=1),
                rmii_mdio=IOPort(name="rmii_mdio", width=1),
            )

        elif phy in gmii_phys:
            self.set_gmii_phy_io(
                gmii_clocks_tx=IOPort(name="gmii_clocks_tx", width=1),
                gmii_clocks_gtx=IOPort(name="gmii_clocks_gtx", width=1),
                gmii_clocks_rx=IOPort(name="gmii_clocks_rx", width=1),
                gmii_rst_n=IOPort(name="gmii_rst_n", width=1),
                gmii_int_n=IOPort(name="gmii_int_n", width=1),
                gmii_mdio=IOPort(name="gmii_mdio", width=1),
                gmii_mdc=IOPort(name="gmii_mdc", width=1),
                gmii_rx_dv=IOPort(name="gmii_rx_dv", width=1),
                gmii_rx_er=IOPort(name="gmii_rx_er", width=1),
                gmii_rx_data=IOPort(name="gmii_rx_data", width=8),
                gmii_tx_en=IOPort(name="gmii_tx_en", width=1),
                gmii_tx_er=IOPort(name="gmii_tx_er", width=1),
                gmii_tx_data=IOPort(name="gmii_tx_data", width=8),
                gmii_col=IOPort(name="gmii_col", width=1),
                gmii_crs=IOPort(name="gmii_crs", width=1),
            )

        elif phy in rgmii_phys:
            self.set_rgmii_phy_io(
                rgmii_clocks_tx=IOPort(name="rgmii_clocks_tx", width=1),
                rgmii_clocks_rx=IOPort(name="rgmii_clocks_rx", width=1),
                rgmii_rst_n=IOPort(name="rgmii_rst_n", width=1),
                rgmii_int_n=IOPort(name="rgmii_int_n", width=1),
                rgmii_mdio=IOPort(name="rgmii_mdio", width=1),
                rgmii_mdc=IOPort(name="rgmii_mdc", width=1),
                rgmii_rx_ctl=IOPort(name="rgmii_rx_ctl", width=1),
                rgmii_rx_data=IOPort(name="rgmii_rx_data", width=4),
                rgmii_tx_ctl=IOPort(name="rgmii_tx_ctl", width=1),
                rgmii_tx_data=IOPort(name="rgmii_tx_data", width=4),
            )

        elif phy in sgmii_phys:
            self.set_sgmii_phy_io(
                sgmii_refclk=IOPort(name="sgmii_refclk", width=1),
                sgmii_rst=IOPort(name="sgmii_rst", width=1),
                sgmii_txp=IOPort(name="sgmii_txp", width=1),
                sgmii_txn=IOPort(name="sgmii_txn", width=1),
                sgmii_rxp=IOPort(name="sgmii_rxp", width=1),
                sgmii_rxn=IOPort(name="sgmii_rxn", width=1),
                sgmii_link_up=IOPort(name="sgmii_link_up", width=1),
            )

    def set_mii_phy_io(
        self,
        mii_clocks_tx,
        mii_clocks_rx,
        mii_rst_n,
        mii_mdio,
        mii_mdc,
        mii_rx_dv,
        mii_rx_er,
        mii_rx_data,
        mii_tx_en,
        mii_tx_data,
        mii_col,
        mii_crs,
    ):
        """
        Sets the signals used to connect to a MII PHY in an Amarnath-native
        design.

        Args:
            mii_clocks_tx (IOPort): Transmit Clock
            mii_clocks_rx (IOPort): Receive Clock
            mii_rst_n (IOPort): PHY Reset
            mii_mdio (IOPort): Management Data
            mii_mdc (IOPort): Management Data Clock
            mii_rx_dv (IOPort): Receive Data Valid
            mii_rx_er (IOPort): Receive Error
            mii_rx_data (IOPort): Receive Data
            mii_tx_en (IOPort): Transmit Enable
            mii_tx_data (IOPort): Transmit Data
            mii_col (IOPort): Collision Detect
            mii_crs (IOPort): Carrier Sense
        """
        self._phy_io = [
            ("i", "mii_clocks_tx", mii_clocks_tx),
            ("i", "mii_clocks_rx", mii_clocks_rx),
            ("o", "mii_rst_n", mii_rst_n),
            ("io", "mii_mdio", mii_mdio),
            ("o", "mii_mdc", mii_mdc),
            ("i", "mii_rx_dv", mii_rx_dv),
            ("i", "mii_rx_er", mii_rx_er),
            ("i", "mii_rx_data", mii_rx_data),
            ("o", "mii_tx_en", mii_tx_en),
            ("o", "mii_tx_data", mii_tx_data),
            ("i", "mii_col", mii_col),
            ("i", "mii_crs", mii_crs),
        ]

    def set_rmii_phy_io(
        self,
        rmii_clocks_ref_clk,
        rmii_rst_n,
        rmii_rx_data,
        rmii_crs_dv,
        rmii_tx_en,
        rmii_tx_data,
        rmii_mdc,
        rmii_mdio,
    ):
        """
        Sets the signals used to connect to a RMII PHY in an Amarnath-native
        design.

        Args:
            rmii_clocks_ref_clk (IOPort): Reference Clock
            rmii_rst_n (IOPort): PHY Reset
            rmii_rx_data (IOPort): Receive Data
            rmii_crs_dv (IOPort): Carrier Sense and Receive Data Valid, multiplexed
            rmii_tx_en (IOPort): Transmit Enable
            rmii_tx_data (IOPort): Transmit Data
            rmii_mdc (IOPort): Management Data Clock
            rmii_mdio (IOPort): Management Data
        """
        self._phy_io = [
            ("i", "rmii_clocks_ref_clk", rmii_clocks_ref_clk),
            ("o", "rmii_rst_n", rmii_rst_n),
            ("i", "rmii_rx_data", rmii_rx_data),
            ("i", "rmii_crs_dv", rmii_crs_dv),
            ("o", "rmii_tx_en", rmii_tx_en),
            ("o", "rmii_tx_data", rmii_tx_data),
            ("o", "rmii_mdc", rmii_mdc),
            ("io", "rmii_mdio", rmii_mdio),
        ]

    def set_gmii_phy_io(
        self,
        gmii_clocks_tx,
        gmii_clocks_gtx,
        gmii_clocks_rx,
        gmii_rst_n,
        gmii_int_n,
        gmii_mdio,
        gmii_mdc,
        gmii_rx_dv,
        gmii_rx_er,
        gmii_rx_data,
        gmii_tx_en,
        gmii_tx_er,
        gmii_tx_data,
        gmii_col,
        gmii_crs,
    ):
        """
        Sets the signals used to connect to a GMII PHY in an Amarnath-native
        design.

        Args:
            gmii_clocks_tx (IOPort): Clock for 10/100 Mbit/s signals.
            gmii_clocks_gtx (IOPort): Clock for gigabit transmit signals
            gmii_clocks_rx (IOPort): Received Clock signal
            gmii_rst_n (IOPort): PHY Reset
            gmii_int_n (IOPort): PHY Interrupt
            gmii_mdio (IOPort): Management Data
            gmii_mdc (IOPort): Management Data Clock
            gmii_rx_dv (IOPort): Receive Data Valid
            gmii_rx_er (IOPort): Receive Error
            gmii_rx_data (IOPort): Receive Data
            gmii_tx_en (IOPort): Transmit Enable
            gmii_tx_er (IOPort): Transmit Error
            gmii_tx_data (IOPort): Transmit Data
            gmii_col (IOPort): Collision Detect
            gmii_crs (IOPort): Carrier Sense
        """
        self._phy_io = [
            ("i", "gmii_clocks_tx", gmii_clocks_tx),
            ("o", "gmii_clocks_gtx", gmii_clocks_gtx),
            ("i", "gmii_clocks_rx", gmii_clocks_rx),
            ("o", "gmii_rst_n", gmii_rst_n),
            ("i", "gmii_int_n", gmii_int_n),
            ("io", "gmii_mdio", gmii_mdio),
            ("o", "gmii_mdc", gmii_mdc),
            ("i", "gmii_rx_dv", gmii_rx_dv),
            ("i", "gmii_rx_er", gmii_rx_er),
            ("i", "gmii_rx_data", gmii_rx_data),
            ("o", "gmii_tx_en", gmii_tx_en),
            ("o", "gmii_tx_er", gmii_tx_er),
            ("o", "gmii_tx_data", gmii_tx_data),
            ("i", "gmii_col", gmii_col),
            ("i", "gmii_crs", gmii_crs),
        ]

    def set_rgmii_phy_io(
        self,
        rgmii_clocks_tx,
        rgmii_clocks_rx,
        rgmii_rst_n,
        rgmii_int_n,
        rgmii_mdio,
        rgmii_mdc,
        rgmii_rx_ctl,
        rgmii_rx_data,
        rgmii_tx_ctl,
        rgmii_tx_data,
    ):
        """
        Sets the signals used to connect to a RGMII PHY in an Amarnath-native
        design.

        Args:
            rgmii_clocks_tx (IOPort): Transmit Clock
            rgmii_clocks_rx (IOPort): Receive Clock
            rgmii_rst_n (IOPort): PHY Reset
            rgmii_int_n (IOPort): PHY Interrupt
            rgmii_mdio (IOPort): Management Data
            rgmii_mdc (IOPort): Management Data Clock
            rgmii_rx_ctl (IOPort): Receive Error and Receive Data Valid, multiplexed
            rgmii_rx_data (IOPort): Receive Data
            rgmii_tx_ctl (IOPort): Transmit Enable and Transmit Error, multiplexed
            rgmii_tx_data (IOPort): Transmit Data
        """
        self._phy_io = [
            ("o", "rgmii_clocks_tx", rgmii_clocks_tx),
            ("i", "rgmii_clocks_rx", rgmii_clocks_rx),
            ("o", "rgmii_rst_n", rgmii_rst_n),
            ("i", "rgmii_int_n", rgmii_int_n),
            ("io", "rgmii_mdio", rgmii_mdio),
            ("o", "rgmii_mdc", rgmii_mdc),
            ("i", "rgmii_rx_ctl", rgmii_rx_ctl),
            ("i", "rgmii_rx_data", rgmii_rx_data),
            ("o", "rgmii_tx_ctl", rgmii_tx_ctl),
            ("o", "rgmii_tx_data", rgmii_tx_data),
        ]

    def set_sgmii_phy_io(
        self,
        sgmii_refclk,
        sgmii_rst,
        sgmii_txp,
        sgmii_txn,
        sgmii_rxp,
        sgmii_rxn,
        sgmii_link_up,
    ):
        """
        Sets the signals used to connect to a SGMII PHY in an Amarnath-native
        design.

        Args:
            sgmii_refclk (IOPort): Reference Clock
            sgmii_rst (IOPort): PHY Reset
            sgmii_txp (IOPort): Transmit Data (Differential)
            sgmii_txn (IOPort): Transmit Data (Differential)
            sgmii_rxp (IOPort): Receive Data (Differential)
            sgmii_rxn (IOPort): Receive Data (Differential)
            sgmii_link_up (IOPort): Link Status

        """
        self._phy_io = [
            ("i", "sgmii_refclk", sgmii_refclk),
            ("i", "sgmii_rst", sgmii_rst),
            ("o", "sgmii_txp", sgmii_txp),
            ("o", "sgmii_txn", sgmii_txn),
            ("i", "sgmii_rxp", sgmii_rxp),
            ("i", "sgmii_rxn", sgmii_rxn),
            ("o", "sgmii_link_up", sgmii_link_up),
        ]

    def elaborate(self, platform):
        m = Module()

        # The DHCP engine in the LiteEth core will request a new IP address
        # when the dhcp_start signal is pulsed. It doesn't want this signal
        # immediately at power-on though, so a timer is used to request an IP
        # one second after power on. The self._clk_freq attribute is used to
        # figure out how many clock cycles that equates to.

        # In my limited testing this seems to be enough time.

        with m.If(self._dhcp_timer < 0):
            m.d.sync += self._dhcp_timer.eq(self._dhcp_timer - 1)

        m.d.sync += self._dhcp_start.eq(self._dhcp_timer == 1)

        # Add the LiteEth core as a submodule
        m.submodules.liteeth = Instance(
            "liteeth_core",
            ("i", "sys_clock", ClockSignal()),
            ("i", "sys_reset", ResetSignal()),
            # PHY connection
            *self._phy_io,
            # DHCP
            # ("o", "dhcp_done", 1),
            # ("o", "dhcp_ip_address", 1),
            ("i", "dhcp_start", self._dhcp_start),
            # ("o", "dhcp_timeout", 1),
            ("i", "ip_address", self._binarize_ip_addr(self._fpga_ip_addr)),
            # UDP Port
            ("i", "udp0_udp_port", self._udp_port),
            # UDP from host
            ("o", "udp0_source_data", self._source_data),
            # ("o", "udp0_source_error", 1),
            ("o", "udp0_source_last", self._source_last),
            ("i", "udp0_source_ready", self._source_ready),
            ("o", "udp0_source_valid", self._source_valid),
            # UDP back to host
            ("i", "udp0_ip_address", self._binarize_ip_addr(self._host_ip_addr)),
            ("i", "udp0_sink_data", self._sink_data),
            ("i", "udp0_sink_last", self._sink_last),
            ("o", "udp0_sink_ready", self._sink_ready),
            ("i", "udp0_sink_valid", self._sink_valid),
        )

        # Add LiteEth module definition if we're in an Amaranth-native workflow
        # If we're in a Verilog-based workflow, then platform will be None, and
        # the module will be added in manta.generate_verilog()
        if platform:
            platform.add_file("liteeth.v", self.generate_liteeth_core())

        m.submodules.source_bridge = source_bridge = UDPSourceBridge()
        m.submodules.sink_bridge = sink_bridge = UDPSinkBridge()

        m.d.comb += source_bridge.data_i.eq(self._source_data)
        m.d.comb += source_bridge.last_i.eq(self._source_last)
        m.d.comb += self._source_ready.eq(source_bridge.ready_o)
        m.d.comb += source_bridge.valid_i.eq(self._source_valid)

        m.d.comb += self._sink_data.eq(sink_bridge.data_o)
        m.d.comb += self._sink_last.eq(sink_bridge.last_o)
        m.d.comb += sink_bridge.ready_i.eq(self._sink_ready)
        m.d.comb += self._sink_valid.eq(sink_bridge.valid_o)

        m.d.comb += sink_bridge.bus_i.eq(self.bus_i)
        m.d.comb += self.bus_o.eq(source_bridge.bus_o)

        return m

    def read(self, addrs):
        """
        Read the data stored in a set of address on Manta's internal memory.
        Addresses must be specified as either integers or a list of integers.
        """

        # Handle a single integer address
        if isinstance(addrs, int):
            return self.read([addrs])[0]

        # Make sure all list elements are integers
        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Read address must be an integer or list of integers.")

        # Send read requests, and get responses
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self._host_ip_addr, self._udp_port))
        chunk_size = 64  # 128
        addr_chunks = split_into_chunks(addrs, chunk_size)
        datas = []

        for addr_chunk in addr_chunks:
            bytes_out = b""
            for addr in addr_chunk:
                bytes_out += int(0).to_bytes(4, byteorder="little")
                bytes_out += int(addr).to_bytes(2, byteorder="little")
                bytes_out += int(0).to_bytes(2, byteorder="little")

            sock.sendto(bytes_out, (self._fpga_ip_addr, self._udp_port))
            data, addr = sock.recvfrom(4 * chunk_size)

            # Split into groups of four bytes
            datas += [int.from_bytes(d, "little") for d in split_into_chunks(data, 4)]

        if len(datas) != len(addrs):
            raise ValueError("Got less data than expected from FPGA.")

        return datas

    def write(self, addrs, datas):
        """
        Write the provided data into the provided addresses in Manta's internal
        memory. Addresses and data must be specified as either integers or a
        list of integers.
        """

        # Handle a single integer address and data
        if isinstance(addrs, int) and isinstance(datas, int):
            return self.write([addrs], [datas])

        # Make sure address and datas are all integers
        if not isinstance(addrs, list) or not isinstance(datas, list):
            raise TypeError(
                "Write addresses and data must be an integer or list of integers."
            )

        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Write addresses must be all be integers.")

        if not all(isinstance(d, int) for d in datas):
            raise TypeError("Write data must all be integers.")

        # Since the FPGA doesn't issue any responses to write requests, we
        # the host's input buffer isn't written to, and we don't need to
        # send the data as chunks as the to avoid overflowing the input buffer.

        # Encode addrs and datas into write requests
        bytes_out = b""
        for addr, data in zip(addrs, datas):
            bytes_out += int(1).to_bytes(4, byteorder="little")
            bytes_out += int(addr).to_bytes(2, byteorder="little")
            bytes_out += int(data).to_bytes(2, byteorder="little")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytes_out, (self._fpga_ip_addr, self._udp_port))

    def generate_liteeth_core(self):
        """
        Generate a LiteEth core by calling a slightly modified form of the
        LiteEth standalone core generator. This passes the contents of the
        'ethernet' section of the Manta configuration file to LiteEth, after
        modifying it slightly.
        """
        liteeth_config = self.to_config()

        # Randomly assign a MAC address if one is not specified in the
        # configuration. This will choose a MAC address in the Locally
        # Administered, Administratively Assigned group. Please reference:
        # https://en.wikipedia.org/wiki/MAC_address#Ranges_of_group_and_locally_administered_addresses

        if "mac_address" not in liteeth_config:
            addr = list(f"{getrandbits(48):012x}")
            addr[1] = "2"
            liteeth_config["mac_address"] = int("".join(addr), 16)
            print(liteeth_config["mac_address"])

        # Force use of DHCP
        liteeth_config["dhcp"] = True

        # Use UDP
        liteeth_config["core"] = "udp"

        # Use 32-bit words. Might be redundant, as I think using DHCP forces
        # LiteEth to use 32-bit words
        liteeth_config["data_width"] = 32

        # Add UDP port
        liteeth_config["udp_ports"] = {
            "udp0": {
                "udp_port": self._udp_port,
                "data_width": 32,
                "tx_fifo_depth": 64,
                "rx_fifo_depth": 64,
            }
        }

        # Generate the core
        from manta.ethernet.liteeth_gen import main

        return main(liteeth_config)
