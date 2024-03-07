from manta import Manta
from time import sleep

manta = Manta("manta.yaml")

i = 0
while True:
    # Turn each LED off
    for j in range(5):
        manta.my_io_core.set_probe(f"LED{j}", 0)

    # Turn one LED back on
    manta.my_io_core.set_probe(f"LED{i}", 1)

    i = (i + 1) % 5
    sleep(0.1)
