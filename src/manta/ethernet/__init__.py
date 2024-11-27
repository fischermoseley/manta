import socket
from random import getrandbits

from amaranth import *
from amaranth.hdl import IOPort

from manta.ethernet.phy_io_defs import phy_io_mapping
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
        phy_io = phy_io_mapping[phy]

        self._phy_io = [
            (p.dir, p.name, IOPort(width=p.width, name=p.name)) for p in phy_io
        ]

    def set_phy_io(self, **kwargs):
        # Given the user's IO, create a list of tuples that can be passed to Instance
        # Only to be used in Amaranth-Native workflows!

        all_phy_io = phy_io_mapping.values()
        all_io_definitions = [io for phy_io in all_phy_io for io in phy_io]
        find_io_def = lambda name: next(
            (iod for iod in all_io_definitions if iod.name == name), None
        )

        self._phy_io = [(find_io_def(k).dir, k, v) for k, v in kwargs.items()]

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
