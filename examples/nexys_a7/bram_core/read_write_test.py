from manta import Manta
from random import randint

m = Manta('manta.yaml')

for addr in range(m.my_lut_ram.size):
    write_data = randint(0, (2**16)-1)
    m.my_lut_ram.write(addr, write_data)

    read_data = m.my_lut_ram.read(addr)
    print(f"test addr: {addr} with data: {write_data}")
    print(f" -> correct data received on readback?: {write_data == read_data}")