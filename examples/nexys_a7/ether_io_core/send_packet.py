from manta import Manta
from scapy.all import *

m = Manta('manta.yaml')
print(m.my_io_core.led.base_addr)


def set_led(val):
    src_mac = "00:e0:4c:68:06:aa"
    dst_mac = "69:69:5a:06:54:91"
    ifc = "en8"

    mypkt = Ether()
    mypkt.src = src_mac
    mypkt.dst = dst_mac
    mypkt.type = 0x1234

    msg = b'\x00\x06' + val.to_bytes(2, 'big')

    mypkt = mypkt / msg
    mypkt.load = msg
    sendpfast(mypkt, iface=ifc)



from time import sleep
led_val = 1
direction = True
while True:
    if direction:
        if led_val == 2**15:
            direction = False

        else:
            led_val = led_val * 2
            set_led(led_val)

    else:
        if led_val == 1:
            direction = True

        else:
            led_val = led_val // 2
            set_led(led_val)

    sleep(0.01)
