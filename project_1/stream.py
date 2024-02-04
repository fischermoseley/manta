import socket
def write(addrs, datas):
    bytes_out = b""
    for addr, data in zip(addrs, datas):
        bytes_out += int(1).to_bytes(4, byteorder="little")
        bytes_out += int(addr).to_bytes(2, byteorder="little")
        bytes_out += int(data).to_bytes(2, byteorder="little")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes_out, (fpga_ip_addr, udp_port))

def read(addrs):
    bytes_out = b""
    for addr in addrs:
        bytes_out += int(0).to_bytes(4, byteorder="little")
        bytes_out += int(addr).to_bytes(2, byteorder="little")
        bytes_out += int(0).to_bytes(2, byteorder="little")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host_ip_addr, udp_port))
    sock.sendto(bytes_out, (fpga_ip_addr, udp_port))
    data, addr = sock.recvfrom(1024)

    return int.from_bytes(data, "little")

if __name__ == "__main__":
    host_ip_addr = "192.168.0.100"
    fpga_ip_addr = "192.168.0.110"
    udp_port = 42069

    for i in range(2**16):
        write([0x0000],[0x0000])
        write([0x0000],[0x0001])
        write([0x0000],[0x0000])
        write([0x0002],[i])
        # print(read([0x0002]))
    # write([0x0002],[0b0101_0101_0101_0101])
    # write([0x0000],[0x0000])
    # write([0x0000],[0x0001])
    # write([0x0000],[0x0000])
