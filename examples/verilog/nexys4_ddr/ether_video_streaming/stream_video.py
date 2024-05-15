import argparse
import numpy as np
from time import sleep
from manta import Manta

m = Manta("manta.yaml")

parser = argparse.ArgumentParser(description="Stream a rendered video to a FPGA on the network.")
parser.add_argument("input_file", type=str, help="Path to input file")
parser.add_argument("--width", type=int, default=128, help="Image width (optional)")
parser.add_argument("--height", type=int, default=128, help="Image height (optional)")
args = parser.parse_args()

addrs = [i for i in range(args.width * args.height)]
frames = np.load(args.input_file).tolist()

for frame in frames:
    m.my_memory.write(addrs, frame)

    # This example doesn't contain any proper control over the rate at which
    # new frames are displayed by the FPGA. That's certinaly possible with
    # some extra logic, but that's been ommitted in order to keep this
    # example simple. As a result, the framerate of the displayed video isn't
    # strictly controlled anywhere.

    # That said, it's possible to add an arbitrary amount of delay between
    # frames to make videos seem like they're going at their native framerate.
    # This is dependent upon the speed of your OS, NIC, and network, so I'll
    # leave it to you to adjust the delay below.

    sleep(0.02)
