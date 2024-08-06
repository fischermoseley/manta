from time import sleep

from manta import *

manta = Manta.from_config("manta.yaml")

i = 0
while True:
    # Turn each LED off
    for j in range(5):
        manta.cores.my_io_core.set_probe(f"LED{j}", 0)

    # Turn one LED back on
    manta.cores.my_io_core.set_probe(f"LED{i}", 1)

    i = (i + 1) % 5
    sleep(0.1)
