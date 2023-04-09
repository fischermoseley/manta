from scapy.all import *

src_mac = "00:e0:4c:68:06:aa"
dst_mac = "69:69:5a:06:54:91"
ifc = "en8"

############

echosvc_etype = 0x1234

mypkt = Ether()
mypkt.src = src_mac
mypkt.dst = dst_mac
mypkt.type = 0x1234

msg = b'\x00\x06\x00\x06'

mypkt = mypkt / msg
for i in range(200):
    mypkt.load = msg
    sendp(mypkt, iface=ifc)