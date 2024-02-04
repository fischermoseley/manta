from manta import Manta
import socket
import time


def configure(ip_address, udp_port):
    m = Manta("manta.yaml")

    # Compute IP address
    octets = [bin(int(o))[2:].zfill(8) for o in ip_address.split(".")]
    ip_binary = int("".join(octets), 2)

    # Set IP address
    m.io_core.set_probe("ip_address", ip_binary)
    m.io_core.set_probe("dhcp_start", 1)
    m.io_core.set_probe("dhcp_start", 0)
    while m.io_core.get_probe("dhcp_done") != 1:
        pass
    print(m.io_core.get_probe("dhcp_ip_address"))

    # Set UDP port
    m.io_core.set_probe("udp_port", udp_port)


def leds_test(ip_address, udp_port):
    m = Manta("manta.yaml")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(0xFF):
        sock.sendto(int(i).to_bytes(1, byteorder="big"), (ip_address, udp_port))
        led = m.io_core.get_probe("led")
        print(f"i:{i} led:{led}")
        time.sleep(0.2)


def send_variable_length_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(0xFF):
        sock.sendto(int(i).to_bytes(i, byteorder="big"), (ip_address, udp_port))
        time.sleep(0.2)


def send_to_host_test(host_ip, udp_port):
    m = Manta("manta.yaml")

    # Set UDP port
    m.io_core.set_probe("udp_port", udp_port)

    # Compute and set destination IP address:
    octets = [bin(int(o))[2:].zfill(8) for o in host_ip.split(".")]
    ip_binary = int("".join(octets), 2)
    m.io_core.set_probe("udp0_ip_address", ip_binary)

    # Send data
    m.io_core.set_probe("udp0_sink_data", 0x21_43_65_87)
    m.io_core.set_probe("udp0_sink_valid", 1)
    m.io_core.set_probe("udp0_sink_valid", 0)


if __name__ == "__main__":
    ip_address = "192.168.0.110"
    udp_port = 42069

    configure(ip_address, udp_port)
    # time.sleep(0.2)
    # for _ in range(64):
    #     send_to_host_test("192.168.0.107", 42069)
    # leds_test(ip_address, udp_port)
    # send_variable_length_test()
