from datetime import datetime
import numpy as np
from vcd import VCDWriter

vcd_file = open("iladata.vcd", "w")
data = np.genfromtxt("iladata.csv", delimiter=',', names=True)

# Use the same datetime format that iVerilog uses
timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")

with VCDWriter(vcd_file, '10 ns', timestamp, "manta") as writer:

    # each probe has a name, width, and writer associated with it
    signals = [{
        "name" : "eth_crsdv",
        "width" : 1,
        "data" : [int(str(i).split('.')[0],2) for i in data['eth_crsdv_IBUF']],
        "var": writer.register_var("manta", "eth_crsdv", "wire", size=1)
    },

    {
        "name" : "eth_rxd",
        "width" : 2,
        "data" : [int(str(i).split('.')[0],2) for i in data['eth_rxd_IBUF10']],
        "var": writer.register_var("manta", "eth_rxd", "wire", size=2)
    },

    ]

    # add the data to each probe in the vcd file
    for timestamp in range(32768):
        # add other signals
        for signal in signals:
            var = signal["var"]
            sample = signal["data"][timestamp]

            writer.change(var, timestamp, sample)

vcd_file.close()