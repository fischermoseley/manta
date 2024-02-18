from amaranth import *
from manta.utils import *
from manta.ethernet.source_bridge import UDPSourceBridge
from manta.ethernet.sink_bridge import UDPSinkBridge
from random import randint
import socket


class EthernetInterface(Elaboratable):
    """
    A module for communicating with Manta over Ethernet, using UDP.

    Provides methods for generating synthesizable logic for the FPGA, as well
    as methods for reading and writing to memory by the host.

    More information available in the online documentation at:
    https://fischermoseley.github.io/manta/ethernet_interface/
    """

    def __init__(self, config):
        self._config = config
        self._fpga_ip_addr = config.get("fpga_ip_addr")
        self._host_ip_addr = config.get("host_ip_addr")
        self._udp_port = config.get("udp_port")
        self._check_config()

        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        self.rmii_clocks_ref_clk = Signal()
        self.rmii_crs_dv = Signal()
        self.rmii_mdc = Signal()
        self.rmii_mdio = Signal()
        self.rmii_rst_n = Signal()
        self.rmii_rx_data = Signal(2)
        self.rmii_tx_data = Signal(2)
        self.rmii_tx_en = Signal()

        self._dhcp_start = Signal()
        self._dhcp_timer = Signal(range(int(100e6)))

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

    def get_top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """
        ports = [
            self.rmii_clocks_ref_clk,
            self.rmii_crs_dv,
            self.rmii_mdc,
            self.rmii_mdio,
            self.rmii_rst_n,
            self.rmii_rx_data,
            self.rmii_tx_data,
            self.rmii_tx_en,
        ]
        return ports

    def _binarize_ip_addr(self, ip_addr):
        octets = [bin(int(o))[2:].zfill(8) for o in ip_addr.split(".")]
        return int("".join(octets), 2)

    def elaborate(self, platform):
        m = Module()

        with m.If(self._dhcp_timer < int(50e6)):
            m.d.sync += self._dhcp_timer.eq(self._dhcp_timer + 1)

        m.d.sync += self._dhcp_start.eq(self._dhcp_timer == (int(50e6) - 2))

        m.submodules.liteeth = Instance(
            "liteeth_core",
            ("i", "sys_clock", ClockSignal()),
            ("i", "sys_reset", ResetSignal()),
            # PHY connection
            ("i", "rmii_clocks_ref_clk", self.rmii_clocks_ref_clk),
            ("i", "rmii_crs_dv", self.rmii_crs_dv),
            ("o", "rmii_mdc", self.rmii_mdc),
            ("io", "rmii_mdio", self.rmii_mdio),
            ("o", "rmii_rst_n", self.rmii_rst_n),
            ("i", "rmii_rx_data", self.rmii_rx_data),
            ("o", "rmii_tx_data", self.rmii_tx_data),
            ("o", "rmii_tx_en", self.rmii_tx_en),
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
        liteeth_config = self._config.copy()

        # Randomly assign a MAC address if one is not specified in the configuration.
        # This will choose a MAC address in the Locally Administered, Administratively Assigned group.
        # For more information, see:
        # https://en.wikipedia.org/wiki/MAC_address#Ranges_of_group_and_locally_administered_addresses

        if "mac_address" not in liteeth_config:
            addr = list(f"{randint(0, (2**48) - 1):012x}")
            addr[1] = "2"
            liteeth_config["mac_address"] = int("".join(addr), 16)

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
