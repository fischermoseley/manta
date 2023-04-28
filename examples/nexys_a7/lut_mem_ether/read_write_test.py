from manta import Manta
from random import randint

m = Manta("manta.yaml")

# for addr in range(m.my_lut_mem.size):
#     write_data = randint(0, (2**16)-1)
#     m.my_lut_mem.write(addr, write_data)

#     read_data = m.my_lut_mem.read(addr)
#     print(f"test addr: {addr} with data: {write_data}")
#     print(f" -> correct data received on readback?: {write_data == read_data}")

# addrs = list(range(m.my_lut_mem.size))
# datas = addrs
# print(m.my_lut_mem.interface.read_batch(addrs))


# internal rage intensifies

# try writing a single register at a time which is known good,
# and then read them back all at once

# m.my_lut_mem.write(39, 42069)
# m.my_lut_mem.write(40, 42070)

# print(m.my_lut_mem.read(39))
# print(m.my_lut_mem.read(40))
# print(m.my_lut_mem.interface.read_batch([39,40]))

# exit()

# ok so i think i kind of understand the issue
# so basically what's happening here is that whatever is in the
# 16's place of the write data at the last write persists in all the reads, meaning

#addrs = list(range(48))
addrs = list(range(m.my_lut_mem.size))
print(addrs)
print('\n')

from time import sleep

for addr in addrs:
   m.my_lut_mem.write(addr, addr)
   sleep(0.1)

print([m.my_lut_mem.read(addr) for addr in addrs])
print('\n')