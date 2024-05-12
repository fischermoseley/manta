from manta import Manta
from time import sleep
from random import randint

m = Manta("manta.yaml")

i = 0
while True:
    i = (i + 1) % 16
    m.my_io_core.set_probe("led", 2**i)

    m.my_io_core.set_probe("led16_r", randint(0, 1))
    m.my_io_core.set_probe("led16_g", randint(0, 1))
    m.my_io_core.set_probe("led16_b", randint(0, 1))

    print(f'Switches: {m.my_io_core.get_probe("sw")}')
    print(f"Buttons:")
    print(f'btnu: {m.my_io_core.get_probe("btnu")}')
    print(f'btnd: {m.my_io_core.get_probe("btnd")}')
    print(f'btnr: {m.my_io_core.get_probe("btnr")}')
    print(f'btnl: {m.my_io_core.get_probe("btnl")}')
    print(f'btnc: {m.my_io_core.get_probe("btnc")}')
    print("")

    sleep(0.1)
