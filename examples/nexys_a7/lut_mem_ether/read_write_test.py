from manta import Manta
from random import randint

m = Manta("manta.yaml")

# The API supports reads/writes to single addresses:
m.my_lut_mem.write(4, 42)
print(m.my_lut_mem.read(4))

# As it does read/writes to multiple addresses at once:
addrs = list(range(m.my_lut_mem.size))
m.my_lut_mem.write(addrs, addrs)
print(m.my_lut_mem.read(addrs))

# And here's a little test to write random data and read it back:
for addr in range(m.my_lut_mem.size):
    write_data = randint(0, (2**16)-1)
    m.my_lut_mem.write(addr, write_data)

    read_data = m.my_lut_mem.read(addr)
    print(f"test addr: {addr} with data: {hex(write_data)}")
    print(f" -> correct data received on readback?: {write_data == read_data}")
    assert write_data == read_data, "data read differs from data written!"