from manta import Manta
from scapy.all import *

m = Manta('manta.yaml')

src_mac = "00:00:00:00:00:00"
dst_mac = "FF:FF:FF:FF:FF:FF"
ifc = "en8"

mypkt = Ether()
mypkt.src = src_mac
mypkt.dst = dst_mac
mypkt.type = 0x0002

msg = b'\x00\x00'

mypkt = mypkt / msg
mypkt.load = msg
p = srp(mypkt, iface=ifc)
p.show()
