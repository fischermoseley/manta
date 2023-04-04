from manta import Manta
m = Manta('examples/nexys_a7/logic_analyzer/manta.yaml')

hdl = m.my_logic_analyzer.generate_logic_analyzer()

with open("test.v", "w") as f:
    f.write(hdl)