![](assets/manta.png)

## Manta: An In-Situ Debugging Tool for Programmable Hardware

Manta is a tool for getting information into and out of FPGAs over an interface like UART or Ethernet. It's primarily intended for debugging, but it's robust enough to be a simple, reliable transport layer between a FPGA and a host machine. It lets you configure a series of cores on a shared bus via a YAML or JSON file, and then provides a Python API to each core, along with vendor-agnostic Verilog HDL to instantiate them on your FPGA.


You might find Manta useful for:

* Verifying specification adherence for connected hardware - your I2S decoder works in simulation, but doesn't in hardware. Manta will help you figure out why.

* Moving generic data between a host and connected FPGA - you're working on a cool new ML accerleator, but you don't want to think about how to get training data and weights out of TensorFlow, across some interface, and into your core.

* Prototyping designs in Python, and incrementally migrating them to hardware. You're working on some real-time signal processing, but you want to prototype it with some sample data in numpy before meticulously implementing everything in Verilog.

Manta is written in Python, and generates Verilog-2001 HDL. It's cross-platform, and its only strict dependencies are pySerial and pyYAML. However, pyvcd is required if you want to export a waveform from the Logic Analyzer core to a `.vcd` file.

## Cores

Manta includes a few cores, configurable to your liking:

* __Logic Analyzer Core__: The host can arm the core, and then when a trigger condition is met, the debug output is wired back to the host, where it's saved as a waveform file. This can then be opened and inspected in a waveform viewer like GTKWave, or directly manipulated in Python using the generated API. This is similar to Xilinx's [Integrated Logic Analyzer (ILA)](https://docs.xilinx.com/r/en-US/ug908-vivado-programming-debugging/ILA) and accompanying [ChipScoPy API](https://xilinx.github.io/chipscopy/2022.2/overview.html) and Intel/Altera's [SignalTap](https://www.intel.com/content/www/us/en/docs/programmable/683819/21-3/logic-analyzer-introduction.html) utility.

* __I/O Core__: This exposes a number of probes that can be read or set, allowing for signals inside the FPGA to be monitored and controlled by the host machine. This is similar to Xilinx's [Virtual IO](https://docs.xilinx.com/v/u/en-US/pg159-vio) core.

* __LUT RAM__ and __BRAM Cores__: Under the hood, Manta is just a bunch of modules sharing a common address and data bus, so cores that add Block RAM and LUT RAM to said bus are also available. More information on this bus configuration is on the [How it Works](how_it_works) page.

These are more explicity described on their individual pages.

## Design Philosophy

* _Things that are easy to misconfigure should be easy to reconfigure_. For instance, it's easy to accidentally put the wrong amount of holdoff in a logic analyzer core and shouldn't require regenerating a bitstream to fix.

* _Don't use macros._ There's a possibility that they'll conflict with something in user code.

* _Autogenerate Verilog 2001 for compatibility._ However, some SystemVerilog 2012 is used for simulation and test.

* _Separate data and operations on it._ This basically means that there shouldn't be much Verilog in the Python, and vice versa. As a result, the code autogeneration is done with a series of HDL templates that have sections filled in by Python. This is done with a bunch of find-and-replace, where hooks in the template file are replaced with the customized Verilog needed at that particular point.

* _Make no assumptions about what the tools can do._ For instance, if you want to make a logic analyzer that has an input probe that's ten billion bits wide, Manta shouldn't complain - it'll leave that to your implementation engine. This allows Manta to maintain portability.

## About
Manta was originally developed as part of my [Master's Thesis at MIT](dspace.mit.edu) in 2023, done under the supervision of Dr. Joe Steinmeyer. But I think it's a neat tool, so I'm still working on it :)