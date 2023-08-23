from manta import Manta
from time import sleep
from random import randint

m = Manta('manta.yaml')

for addr in range(1024):
    number = randint(0,65535)
    m.my_block_memory.write(addr, number)

    readback = m.my_block_memory.read(addr)

    if readback == number:
        print(f"Success! Wrote and read back {hex(number)} from {hex(addr)}")

    else:
        print(f"Failure! Wrote {hex(number)} to {hex(addr)}, but received {hex(readback)}")
        exit()
