from random import randint
from time import sleep

from manta import *

manta = Manta.from_config("manta.yaml")

i = 0
while True:
    i = (i + 1) % 16
    manta.cores.my_io_core.set_probe("led", 2**i)

    manta.cores.my_io_core.set_probe("led16_r", randint(0, 1))
    manta.cores.my_io_core.set_probe("led16_g", randint(0, 1))
    manta.cores.my_io_core.set_probe("led16_b", randint(0, 1))

    print(f'Switches: {manta.cores.my_io_core.get_probe("sw")}')
    print(f"Buttons:")
    print(f'btnu: {manta.cores.my_io_core.get_probe("btnu")}')
    print(f'btnd: {manta.cores.my_io_core.get_probe("btnd")}')
    print(f'btnr: {manta.cores.my_io_core.get_probe("btnr")}')
    print(f'btnl: {manta.cores.my_io_core.get_probe("btnl")}')
    print(f'btnc: {manta.cores.my_io_core.get_probe("btnc")}')
    print("")

    sleep(0.1)
