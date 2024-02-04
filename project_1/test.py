from manta import Manta
m = Manta("manta.yaml")

print(bin(m.io_core.get_probe("sw")))
m.io_core.set_probe("led", 4)