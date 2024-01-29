from manta import Manta
import socket
import time

if __name__ == "__main__":
    ip_address = "192.168.0.110"
    udp_port = 42069

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for i in range(256):
        data = [0, 0]
        data = [int(d).to_bytes(4, byteorder="big") for d in data]
        data = b"".join(data)
        print(data)
        sock.sendto(data, (ip_address, udp_port))
        # time.sleep(0.2)
