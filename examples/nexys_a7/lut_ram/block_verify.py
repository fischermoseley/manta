import serial
from time import sleep
import random

usb_device = "/dev/tty.usbserial-2102926963071"


def write_block(data, base_addr = 0):
    msg = b''

    for addr, data in enumerate(data):
        addr_str = '{:04X}'.format(base_addr + addr)
        data_str = '{:04X}'.format(data)
        msg += f"M{addr_str}{data_str}\r\n".encode('ascii')

    with serial.Serial(usb_device, 115200) as ser:
        ser.write(msg)


def read_block(addrs, base_addr):
    msg = b''

    for addr in range(addrs):
        addr_str = '{:04X}'.format(base_addr + addr)
        msg += f"M{addr_str}\r\n".encode('ascii')

    with serial.Serial(usb_device, 115200) as ser:
        ser.write(msg)
        response = ser.read(7*addrs)
        response = response.decode('ascii').replace('\r\n', '').split('M')
        return [int(i, 16) for i in response if i]

if __name__ == "__main__":
    for i in range(1000):
        test_data = [random.randint(0, 65535) for i in range(32)]
        write_block(test_data, 0)
        
        received = read_block(32, 0)
        print(i)

        if(received != test_data):
            exit()

