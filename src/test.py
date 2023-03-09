from manta import Manta

m = Manta('/Users/fischerm/fpga/manta/examples/nexys_a7/single_lut_ram/manta.yaml')
m.generate_hdl('inspecto_time.v')