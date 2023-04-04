from manta import Manta

m = Manta('manta.yaml')

# setup trigger to trigger when moe = 1:
m.my_logic_analyzer.interface.write_register(0, 0) # set state to IDLE
m.my_logic_analyzer.interface.write_register(6, 8) # set operation to eq
m.my_logic_analyzer.interface.write_register(7, 1) # set argument to 1

# read that back
print(m.my_logic_analyzer.interface.read_register(0))
print(m.my_logic_analyzer.interface.read_register(6))
print(m.my_logic_analyzer.interface.read_register(7))


# start the capture
m.my_logic_analyzer.interface.write_register(0, 1) # set state to START_CAPTURE
print(m.my_logic_analyzer.interface.read_register(0))

# display sample data
for i in range(m.my_logic_analyzer.sample_depth):
    data = m.my_logic_analyzer.interface.read_register(i)
    print(f"addr: {i}  data: {data}")