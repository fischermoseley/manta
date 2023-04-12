from manta import Manta
m = Manta('manta.yaml')

bram_def = m.my_bram.hdl_def()

with open("block_memory.v", "w") as f:
    f.write(bram_def)

print(m.my_bram.hdl_top_level_ports())