from ..hdl_utils import *

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
        self.send_packet = sendp
        if "tcpreplay" in config:
            assert isinstance(config["tcpreplay"], bool), \
                "tcpreplay configuration option must be boolean!"
            self.send_packet = sendpfast if config["tcpreplay"] else sendp

        self.verbose = False
        if "verbose" in config:
            assert isinstance(config["verbose"], bool), \
                "verbose configuration option must be boolean!"
            self.verbose = config["verbose"]

    def read_register(self, addr):
        pkt = Ether()
        pkt.src = self.host_mac
        pkt.dst = self.fpga_mac
        pkt.type = self.ethertype

        # one byte of rw, two bytes of address, and 44 of padding
        # makes the 46 byte minimum length
        msg = b'\x00' + addr.to_bytes(2, 'big') + 43*b'\x00'

        pkt = pkt / msg
        pkt.load = msg

        sniffer = AsyncSniffer(iface = self.iface, filter=f"ether src {self.fpga_mac}")
        sniffer.start()
        sleep(0.1)

        self.send_packet(pkt, iface=self.iface, verbose = 0)

        results = sniffer.stop()

        assert len(results) == 1, "Received more packets than expected!"

        raw_response_bytes = bytes(results[0].payload)[3:5]
        return int.from_bytes(raw_response_bytes, 'big')

    def write_register(self, addr, data):
        pkt = Ether()
        pkt.src = self.host_mac
        pkt.dst = self.fpga_mac
        pkt.type = self.ethertype

        # one byte of rw, two bytes of address, two bytes of
        # data, and 42 of padding makes the 46 byte
        # minimum length
        msg = b'\x01' + addr.to_bytes(2, 'big') + data.to_bytes(2, 'big') + 41*b'\x00'

        pkt = pkt / msg
        pkt.load = msg
        self.send_packet(pkt, iface=self.iface, verbose = self.verbose)

    def read_batch(self, addrs):
        # Prepare packets to read from addresses
        pkts = []
        for addr in addrs:
            pkt = Ether()
            pkt.src = self.host_mac
            pkt.dst = self.fpga_mac
            pkt.type = self.ethertype

            # one byte of rw, two bytes of address, and 44 of padding
            # makes the 46 byte minimum length
            msg = b'\x00' + addr.to_bytes(2, 'big') + 43*b'\x00'

            pkt = pkt / msg
            pkt.load = msg
            pkts.append(pkt)

        # Start sniffer in another thread, send packets, grab responses
        sniffer = AsyncSniffer(iface = self.iface, count = len(addrs), filter=f"ether src {self.fpga_mac}")
        sniffer.start()
        sleep(0.1)
        sendp(pkts, iface=self.iface, verbose = 0, inter = 0.05)
        sniffer.join()
        results = sniffer.results

        assert len(results) == len(addrs), "Received more packets than expected!"

        # #print(raw(results[1]))
        # for packet in results:
        #     hexdump(packet)
        #     print( [i for i in bytes(packet.payload)] )
        #     print( [i for i in raw(packet)] )
        #     print("\n")

        # Parse packets
        datas = []
        for packet in results:
            raw_response_bytes = bytes(packet.payload)[3:5]
            data = int.from_bytes(raw_response_bytes, 'big')
            datas.append(data)

        return datas

    def write_batch(self, addrs, datas):
        assert len(addrs) == len(datas), \
            "Number of addresses provided is unequal to number of data provided!"

        pkts = []
        for addr, data in zip(addrs, datas):
            pkt = Ether()
            pkt.src = self.host_mac
            pkt.dst = self.fpga_mac
            pkt.type = self.ethertype

            # one byte of rw, two bytes of address, two bytes of data, and 41
            # bytes of paddding make the 46 byte limit.
            msg = b'\x01' + addr.to_bytes(2, 'big') + data.to_bytes(2, 'big') + 41*b'\x00'

            pkt = pkt / msg
            pkt.load = msg
            pkts.append(pkt)

        self.send_packet(pkts, iface=self.iface, verbose = 0)

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