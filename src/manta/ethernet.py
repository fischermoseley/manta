from amaranth import *
from manta.utils import *
import socket


class EthernetInterface(Elaboratable):
    def __init__(self, config):
        self.fpga_ip_addr = config["fpga_ip_addr"]
        self.host_ip_addr = config["host_ip_addr"]
        self.udp_port = config["udp_port"]

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

        self.dhcp_start = Signal()
        self.dhcp_timer = Signal(range(int(100e6)))

        self.source_data = Signal(32)
        self.source_last = Signal()
        self.source_ready = Signal()
        self.source_valid = Signal()

        self.sink_data = Signal(32)
        self.sink_last = Signal()
        self.sink_ready = Signal()
        self.sink_valid = Signal()

    def get_top_level_ports(self):
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

    def binarize_ip_addr(self, ip_addr):
        octets = [bin(int(o))[2:].zfill(8) for o in ip_addr.split(".")]
        return int("".join(octets), 2)

    def elaborate(self, platform):
        m = Module()

        with m.If(self.dhcp_timer < 15):
            m.d.sync += self.dhcp_timer.eq(self.dhcp_timer + 1)

        m.d.sync += self.dhcp_start.eq(self.dhcp_timer == 14)

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
            ("i", "dhcp_start", self.dhcp_start),
            # ("o", "dhcp_timeout", 1),
            ("i", "ip_address", self.binarize_ip_addr(self.fpga_ip_addr)),
            # UDP Port
            ("i", "udp0_udp_port", self.udp_port),
            # UDP from host
            ("o", "udp0_source_data", self.source_data),
            # ("o", "udp0_source_error", 1),
            ("o", "udp0_source_last", self.source_last),
            ("i", "udp0_source_ready", self.source_ready),
            ("o", "udp0_source_valid", self.source_valid),
            # UDP back to host
            ("i", "udp0_ip_address", self.binarize_ip_addr(self.host_ip_addr)),
            ("i", "udp0_sink_data", self.sink_data),
            ("i", "udp0_sink_last", self.sink_last),
            ("o", "udp0_sink_ready", self.sink_ready),
            ("i", "udp0_sink_valid", self.sink_valid),
        )

        m.submodules.source_bridge = source_bridge = UDPSourceBridge()
        m.submodules.sink_bridge = sink_bridge = UDPSinkBridge()

        m.d.comb += source_bridge.data_i.eq(self.source_data)
        m.d.comb += source_bridge.last_i.eq(self.source_last)
        m.d.comb += self.source_ready.eq(source_bridge.ready_o)
        m.d.comb += source_bridge.valid_i.eq(self.source_valid)

        m.d.comb += self.sink_data.eq(sink_bridge.data_o)
        m.d.comb += self.sink_last.eq(sink_bridge.last_o)
        m.d.comb += sink_bridge.ready_i.eq(self.sink_ready)
        m.d.comb += self.sink_valid.eq(sink_bridge.valid_o)

        m.d.comb += sink_bridge.bus_i.eq(self.bus_i)
        m.d.comb += self.bus_o.eq(source_bridge.bus_o)

        return m

    def read(self, addrs):
        """
        Read the data stored in a set of address on Manta's internal memory. Addresses
        must be specified as either integers or a list of integers.
        """

        # Handle a single integer address
        if isinstance(addrs, int):
            return self.read([addrs])[0]

        # Make sure all list elements are integers
        if not all(isinstance(a, int) for a in addrs):
            raise ValueError("Read address must be an integer or list of integers.")

        # Send read requests, and get responses
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host_ip_addr, self.udp_port))
        chunk_size = 128
        addr_chunks = split_into_chunks(addrs, chunk_size)
        datas = []

        for addr_chunk in addr_chunks:
            bytes_out = b""
            for addr in addr_chunk:
                bytes_out += int(0).to_bytes(4, byteorder="little")
                bytes_out += int(addr).to_bytes(2, byteorder="little")
                bytes_out += int(0).to_bytes(2, byteorder="little")

            sock.sendto(bytes_out, (self.fpga_ip_addr, self.udp_port))
            data, addr = sock.recvfrom(4 * chunk_size)

            # Split into groups of four bytes
            datas += [int.from_bytes(d, "little") for d in split_into_chunks(data, 4)]

        return datas

    def write(self, addrs, datas):
        """
        Write the provided data into the provided addresses in Manta's internal memory.
        Addresses and data must be specified as either integers or a list of integers.
        """

        # Handle a single integer address and data
        if isinstance(addrs, int) and isinstance(datas, int):
            return self.write([addrs], [datas])

        # Make sure address and datas are all integers
        if not isinstance(addrs, list) or not isinstance(datas, list):
            raise ValueError(
                "Write addresses and data must be an integer or list of integers."
            )

        if not all(isinstance(a, int) for a in addrs):
            raise ValueError("Write addresses must be all be integers.")

        if not all(isinstance(d, int) for d in datas):
            raise ValueError("Write data must all be integers.")

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
        sock.sendto(bytes_out, (self.fpga_ip_addr, self.udp_port))


class UDPSourceBridge(Elaboratable):
    def __init__(self):
        self.bus_o = Signal(InternalBus())

        self.data_i = Signal(32)
        self.last_i = Signal()
        self.ready_o = Signal()
        self.valid_i = Signal()

    def elaborate(self, platform):
        m = Module()

        state = Signal()  # can either be 0, for read/write, or 1, for data
        rw_buf = Signal().like(self.bus_o.rw)

        # Can always take more data
        m.d.sync += self.ready_o.eq(1)

        m.d.sync += self.bus_o.eq(0)
        with m.If(self.valid_i):
            m.d.sync += state.eq(~state)

            with m.If(state == 0):
                m.d.sync += rw_buf.eq(self.data_i)

            with m.Else():
                m.d.sync += self.bus_o.addr.eq(self.data_i[:16])
                m.d.sync += self.bus_o.data.eq(self.data_i[16:])
                m.d.sync += self.bus_o.rw.eq(rw_buf)
                m.d.sync += self.bus_o.valid.eq(1)
                m.d.sync += self.bus_o.last.eq(self.last_i)

        return m


class UDPSinkBridge(Elaboratable):
    def __init__(self):
        self.bus_i = Signal(InternalBus())

        self.data_o = Signal(32)
        self.last_o = Signal()
        self.ready_i = Signal()
        self.valid_o = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.sync += self.data_o.eq(0)
        m.d.sync += self.last_o.eq(0)
        m.d.sync += self.valid_o.eq(0)

        with m.If( (self.bus_i.valid) & (~self.bus_i.rw)):
            m.d.sync += self.data_o.eq(self.bus_i.data)
            m.d.sync += self.last_o.eq(self.bus_i.last)
            m.d.sync += self.valid_o.eq(1)

        return m
