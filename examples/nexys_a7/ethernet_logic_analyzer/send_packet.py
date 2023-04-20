from manta import Manta
from scapy.all import *

m = Manta('manta.yaml')


def set_led(val):
    src_mac = "00:00:00:00:00:00"
    dst_mac = "FF:FF:FF:FF:FF:FF"
    ifc = "en8"

    mypkt = Ether()
    mypkt.src = src_mac
    mypkt.dst = dst_mac
    mypkt.type = 0x1234

    msg = b'\x56\x78' + val.to_bytes(2, 'big')

    mypkt = mypkt / msg
    mypkt.load = msg
    sendpfast(mypkt, iface=ifc)

while(True):
    set_led(0)
