![](assets/manta.png)

## Manta: An In-Situ Debugging Tool for Programmable Hardware
![functional_simulation](https://github.com/fischermoseley/manta/actions/workflows/functional_simulation.yml/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manta is a tool for debugging FPGA designs over an interface like UART or Ethernet. It works by allowing the user to instantiate a number of debug cores in a design, and exposes a Python interface to them. This permits rapid prototyping of logic in Python, and a means of incrementally migrating it to HDL. The cores are described below.

Manta is written in Python, and generates Verilog-2001 HDL. It's cross-platform, and its only dependencies are pySerial and pyYAML.

## Cores

### Logic Analayzer Core
Manta's downlink mode works by taking a YAML/JSON file describing the ILA configuration, and autogenerating a debug core with SystemVerilog. This gets included in the rest of the project's HDL, and is synthesized and flashed on the FPGA. It can then be controlled by a host machine connected over a serial port. The host can arm the core, and then when a trigger condition is met, the debug output is wired back to the host, where it's saved as a waveform file. This can then be opened and inspected in a waveform viewer like GTKWave.

This is similar to Xilinx's Integrated Logic Analyzer (ILA) and Intel/Altera's SignalTap utility.

### I/O Core

### LUT RAM Core

### BRAM Core


## Getting Started
Manta is installed with `pip3 install mantaray`. Or at least it will be, once it's out of alpha. For now, it's installable with `pip install -i https://test.pypi.org/simple/ mantaray`, which just pulls from the PyPI testing registry.

## Examples
Examples can be found under `examples/`. These target the Xilinx Series 7 FPGAs on the [Nexys A7](https://digilent.com/reference/programmable-logic/nexys-a7/start)/[Nexys4 DDR](https://digilent.com/reference/programmable-logic/nexys-4-ddr/start) and the Lattice iCE40 on the [Icestick](https://www.latticesemi.com/icestick).

## Design Philosophy
- Things that are easy to break should be easy to fix. For instance, it's pretty easy to put the wrong number of clock cycles of holdoff in your configuration, but it's a lot harder to accidentally put the wrong number of stop bits in your serial port. Manta supports changing the former post-upload, but not the latter.
- Features are added when they're needed. We won't add features until there's been a use case shown that would benefit from them. This keeps manta lightweight.
- Trust the interface. In the name of simplicity, we don't implement a ton of error checking. If this proves to be a problem, we'll fix it, inline with the philosophy above.
- Don't use macros - there's a possibility that they'll conflict with something in user code.
- Use Verilog 2001 for source for compatibility. Manta uses SystemVerilog 2012 for simulation and test, however.

## About
Manta was originally developed as part of my [Master's Thesis at MIT](dspace.mit.edu) in 2023, done under the supervision of Joe Steinmeyer. But I think it's a neat tool, so I'm still working on it :)