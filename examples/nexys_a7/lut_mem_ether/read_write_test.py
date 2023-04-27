from manta import Manta
from random import randint

m = Manta('manta.yaml')

from manta import Manta
from time import sleep

m = Manta("manta.yaml")
print(m.my_lut_mem.read(0))

m.my_lut_mem.write(0, 5)

print(m.my_lut_mem.read(0))

# for addr in range(m.my_lut_mem.size):
#     write_data = randint(0, (2**16)-1)
#     m.my_lut_mem.write(addr, write_data)

#     read_data = m.my_lut_mem.read(addr)
#     print(f"test addr: {addr} with data: {write_data}")
#     print(f" -> correct data received on readback?: {write_data == read_data}")