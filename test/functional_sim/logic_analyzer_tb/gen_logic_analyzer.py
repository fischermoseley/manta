from manta import Manta

m = Manta('manta.yaml')
la = m.my_logic_analyzer.hdl_def()

with open('logic_analyzer.v', 'w') as f:
    f.write(la)