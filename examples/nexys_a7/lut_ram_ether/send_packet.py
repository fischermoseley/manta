from scapy.all import *

src_mac = "00:E0:4C:68:1E:0C" # for manta.mit.edu's ethernet adapter
dst_mac = "69:69:5A:06:54:91"
ifc = "enx00e04c681e0c"

def read_register(addr):
    pkt = Ether()
    pkt.src = src_mac
    pkt.dst = dst_mac
    pkt.type = 0x0002

    # two bytes of address, and 44 of padding
    # makes the 46 byte minimum length
    msg = addr.to_bytes(2, 'big') + 44*b'\x00'

    pkt = pkt / msg
    pkt.load = msg

    sniffer = AsyncSniffer(iface = ifc, filter="ether src 69:69:5a:06:54:91")
    sniffer.start()
    from time import sleep
    time.sleep(0.1)
    sendp(pkt, iface=ifc, verbose = 0)
    results = sniffer.stop()

    assert len(results) == 1, "Received more packets than expected!"

    for packet in results:
        raw_response_bytes = bytes(packet.payload)[0:2]
        data = int.from_bytes(raw_response_bytes, 'big')
        return data

def write_register(addr, data):
    pkt = Ether()
    pkt.src = src_mac
    pkt.dst = dst_mac
    pkt.type = 0x0004

    # two bytes of address, two bytes of
    # data, and 42 of padding makes the 46 byte
    # minimum length
    msg = addr.to_bytes(2, 'big') + data.to_bytes(2, 'big') + 42*b'\x00'

    pkt = pkt / msg
    pkt.load = msg
    sendp(pkt, iface=ifc, verbose = 0)

def read_batch(addrs):
    pkts = []
    for addr in addrs:
        pkt = Ether()
        pkt.src = src_mac
        pkt.dst = dst_mac
        pkt.type = 0x0002

        # two bytes of address, and 44 of padding
        # makes the 46 byte minimum length
        msg = addr.to_bytes(2, 'big') + 44*b'\x00'

        pkt = pkt / msg
        pkt.load = msg
        pkts.append(pkt)

    sniffer = AsyncSniffer(iface = ifc, count = len(addrs), filter="ether src 69:69:5a:06:54:91")
    sniffer.start()
    from time import sleep
    time.sleep(0.1)

    sendp(pkts, iface=ifc, verbose = 0)
    sniffer.join()
    results = sniffer.results

    assert len(results) == len(addrs), "Received more packets than expected!"

    datas = []
    for packet in results:
        raw_response_bytes = bytes(packet.payload)[0:2]
        data = int.from_bytes(raw_response_bytes, 'big')
        datas.append(data)

    return datas

def write_batch(addrs, data):
    pkts = []
    for i in range(len(addrs)):
        pkt = Ether()
        pkt.src = src_mac
        pkt.dst = dst_mac
        pkt.type = 0x0002

        addr = addrs[i]
        data = datas[i]

        # two bytes of address, two bytes of
        # data, and 42 of padding makes the 46 byte
        # minimum length
        msg = addr.to_bytes(2, 'big') + data.to_bytes(2, 'big') + 42*b'\x00'

        pkt = pkt / msg
        pkt.load = msg

    sendp(pkts, iface=ifc, verbose = 0)


from time import sleep
if __name__ == "__main__":
    for addr in range(64):
        data = addr
        write_register(addr, data)
        retval = read_register(addr)
        if retval != addr:
            print(f"ERROR: sent {data} got {retval}")

        else:
            print(f"SUCCESS: sent {data} got {retval}")

    # addrs = [i for i in range(64)]
    # datas = addrs
    # write_batch(addrs, datas)
    # print("done")
    # retvals = read_batch(addrs)
    # print(retvals)

