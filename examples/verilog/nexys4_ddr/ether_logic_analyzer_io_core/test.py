from manta import *

manta = Manta.from_config("manta.yaml")

print(manta.cores.my_io_core.get_probe("sw"))
manta.cores.my_io_core.set_probe("led", 4)
