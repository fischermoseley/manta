from manta import Manta
import pickle

m = Manta('manta.yaml')
# capture = m.my_logic_analyzer.capture()

# with open("capture.pkl", "wb") as f:
#     pickle.dump(capture, f)

with open("capture.pkl", "rb") as f:
    capture = pickle.load(f)

m.my_logic_analyzer.export_vcd(capture, "capture.vcd")
m.my_logic_analyzer.export_mem(capture, "capture.mem")
