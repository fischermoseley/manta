from ..utils import *

# Lazy and selective imports for quick builds!
from scapy.interfaces import get_if_list
from scapy.arch import get_if_hwaddr
from scapy.layers.l2 import Ether
from scapy.sendrecv import AsyncSniffer, sendp, sendpfast
from time import sleep

from scapy.all import *

class EthernetInterface:
    def __init__(self, config):
        # Warn if unrecognized options have been given
        for option in config:
            if option not in ["interface", "host_mac", "fpga_mac", "ethertype", "tcpreplay", "verbose"]:
                print(f"Warning: Ignoring unrecognized option '{option}' in Ethernet interface.")

        # Obtain interface.
        assert "interface" in config, "No interface provided for Ethernet core."
        if config["interface"] not in get_if_list():
            print(f"Warning: Interface specified is not detected by the host.")
        self.iface = config["interface"]

        # Obtain Host MAC address
        if self.iface in get_if_list():
            self.host_mac = get_if_hwaddr(self.iface)
        else:
            assert "host_mac" in config, \
                "Can't automatically detect host mac address from interface, host_mac must be manually provided"
            self.host_mac = config["host_mac"]

        # Obtain FPGA MAC address
        #  - the default address is a locally administered unicast address,
        #     which is an important distinction. please refer to:
        #    https://en.wikipedia.org/wiki/MAC_address#Ranges_of_group_and_locally_administered_addresses
        self.fpga_mac = "12:34:56:78:9A:BC"
        if "fpga_mac" in config:
            self.fpga_mac = config["fpga_mac"]

        # Obtain Ethertype
        #  - the default ethertype being used is reserved for local
        #    experimentation by the IEEE - and might not make it beyond
        #    your NIC as a result.
        self.ethertype = 0x88B5
        if "ethertype" in config:
            self.ethertype = int(config["ethertype"], 16)

        # Set whether we use tcpreplay for faster packet blasting
        if "tcpreplay" in config:
            assert isinstance(config["tcpreplay"], bool), \
                "tcpreplay configuration option must be boolean!"

            if config["tcpreplay"]:
                self.send_packets = lambda p: sendpfast(p, iface=self.iface)

            else:
                self.send_packets = lambda p: sendp(p, iface=self.iface, verbose=0)

        else:
            self.send_packets = lambda p: sendp(p, iface=self.iface, verbose=0)


        self.verbose = False
        if "verbose" in config:
            assert isinstance(config["verbose"], bool), \
                "verbose configuration option must be boolean!"
            self.verbose = config["verbose"]

    def read(self, addr):
        # Perform type checks, output list of addresses
        if isinstance(addr, int):
            addrs = [addr]

        elif isinstance(addr, list):
            assert all(isinstance(a, int) for a in addr), \
                "Read addresses must be integer or list of integers."
            addrs = addr

        else:
            raise ValueError("Read addresses must be integer or list of integers.")

        # Prepare packets with read requests
        request_pkts = []
        for a in addrs:
            pkt = Ether()
            pkt.src = self.host_mac
            pkt.dst = self.fpga_mac
            pkt.type = self.ethertype

            # one byte of rw, two bytes of address, and 44 of padding
            # makes the 46 byte minimum length
            msg = b'\x00' + a.to_bytes(2, 'big') + 43*b'\x00'

            pkt = pkt / msg
            pkt.load = msg
            request_pkts.append(pkt)

        # Start sniffer in another thread, send packets, grab responses
        sniffer = AsyncSniffer(iface = self.iface, count = len(addrs), filter=f"ether src {self.fpga_mac}")
        sniffer.start()
        sleep(0.5)
        self.send_packets(request_pkts)
        sniffer.join()
        response_pkts = sniffer.results
        assert len(response_pkts) == len(request_pkts), "Received wrong number of packets!"

        # Get read data by pulling bytes 3 and 4 from the returned packets
        # payload, and interpreting it as big endian
        get_read_data = lambda x: int.from_bytes(bytes(x.payload)[3:5], 'big')
        read_data = [get_read_data(pkt) for pkt in response_pkts]

        if len(read_data) == 1:
            return read_data[0]

        else:
            return read_data

    def write(self, addr, data):
        # Perform type checks, output list of addresses
        if isinstance(addr, int):
            assert isinstance(data, int), \
                "Data must also be integer if address is integer."
            addrs = [addr]
            datas = [data]

        elif isinstance(addr, list):
            assert all(isinstance(a, int) for a in addr), \
                "Write addresses must be integer or list of integers."

            assert all(isinstance(d, int) for d in data), \
                "Write data must be integer or list of integers."

            assert len(addr) == len(data), \
                "There must be equal number of write addresses and data."

            addrs = addr
            datas = data

        else:
            raise ValueError("Write addresses and data must be integer or list of integers.")

        # Prepare packets with write requests
        request_pkts = []
        for a, d in zip(addrs, datas):
            pkt = Ether()
            pkt.src = self.host_mac
            pkt.dst = self.fpga_mac
            pkt.type = self.ethertype

            # one byte of rw, two bytes of address, two bytes of data, and 42 of padding
            # makes the 46 byte minimum length
            msg = b'\x01' + a.to_bytes(2, 'big') + d.to_bytes(2, 'big') + 41*b'\x00'

            pkt = pkt / msg
            pkt.load = msg
            request_pkts.append(pkt)

        self.send_packets(request_pkts)

    def hdl_top_level_ports(self):
        return ["input wire crsdv", \
                "input wire [1:0] rxd", \
                "output reg txen", \
                "output reg [1:0] txd"]

    def rx_hdl_def(self):
        tx =  VerilogManipulator("ether_iface/ethernet_rx.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/mac_rx.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/ether.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/bitorder.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/firewall.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/aggregate.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/crc32.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/cksum.v").get_hdl() + "\n"
        return tx

    def tx_hdl_def(self):
        tx =  VerilogManipulator("ether_iface/ethernet_tx.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/mac_tx.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/bitorder.v").get_hdl() + "\n"
        tx += VerilogManipulator("ether_iface/crc32.v").get_hdl() + "\n"
        return tx

    def rx_hdl_inst(self):
        rx = VerilogManipulator("ether_iface/ethernet_rx_inst_tmpl.v")

        fpga_mac_verilog_literal = "48'h" + self.fpga_mac.replace(":", "_").upper()
        rx.sub(fpga_mac_verilog_literal, "/* FPGA_MAC */")

        ethertype_verilog_literal = f"16'h{self.ethertype:02X}"
        rx.sub(ethertype_verilog_literal, "/* ETHERTYPE */")

        return rx.get_hdl()

    def tx_hdl_inst(self):
        tx = VerilogManipulator("ether_iface/ethernet_tx_inst_tmpl.v")

        fpga_mac_verilog_literal = "48'h" + self.fpga_mac.replace(":", "_").upper()
        tx.sub(fpga_mac_verilog_literal, "/* FPGA_MAC */")

        host_mac_verilog_literal = "48'h" + self.host_mac.replace(":", "_").upper()
        tx.sub(host_mac_verilog_literal, "/* HOST_MAC */")

        ethertype_verilog_literal = f"16'h{self.ethertype:02X}"
        tx.sub(ethertype_verilog_literal, "/* ETHERTYPE */")

        return tx.get_hdl()