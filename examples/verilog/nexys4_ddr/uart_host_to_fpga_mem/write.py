from manta import *

manta = Manta.from_config("manta.yaml")

# Memory addresses can be written to in Python, and then be read out by
# flipping the switches on the FPGA, and watching the LEDs update!

manta.cores.my_memory.write(0, 1)
