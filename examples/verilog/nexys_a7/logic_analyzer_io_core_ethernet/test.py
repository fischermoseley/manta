from manta import Manta

m = Manta("manta.yaml")

print(m.my_io_core.get_probe("sw"))
m.my_io_core.set_probe("led", 4)
