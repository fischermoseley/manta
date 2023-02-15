![](assets/manta.png)

## Manta: An In-Situ Debugging Tool for Programmable Hardware
![functional_simulation](https://github.com/fischermoseley/manta/actions/workflows/functional_simulation.yml/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manta is a tool for debugging FPGA designs over an interface like UART or Ethernet. It has two modes for doing this, downlink and uplink. The downlink mode feels similar to a logic analyzer, in that Manta provides a waveform view of a configurable set of signals, which get captured when some trigger condition is met. The uplink mode allows a host machine to remotely set values of registers on the FPGA via a python interface. This permits rapid prototyping of logic in Python, and a means of incrementally migrating it to HDL. A more detailed description of each mode is below.

Manta is written in Python, and generates SystemVerilog HDL. It's cross-platform, and its only dependencies are pySerial and pyYAML. The SystemVerilog templates are included in the Python source, so only a single python file must be included in your project.

## Design Philosophy
- Things that are easy to break should be easy to fix. For instance, it's pretty easy to put the wrong number of clock cycles of holdoff in your configuration, but it's a lot harder to accidentally put the wrong number of stop bits in your serial port. Manta supports changing the former post-upload, but not the latter.
- Features are added when they're needed. We won't add features until there's been a use case shown that would benefit from them. This keeps manta lightweight.

## Downlink
Manta's downlink mode works by taking a YAML/JSON file describing the ILA configuration, and autogenerating a debug core with SystemVerilog. This gets included in the rest of the project's HDL, and is synthesized and flashed on the FPGA. It can then be controlled by a host machine connected over a serial port. The host can arm the core, and then when a trigger condition is met, the debug output is wired back to the host, where it's saved as a waveform file. This can then be opened and inspected in a waveform viewer like GTKWave.

This is similar to Xilinx's Integrated Logic Analyzer (ILA) and Intel/Altera's SignalTap utility.

## Getting Started
Manta is installed with `pip3 install mantaray`. Or at least it will be, once it's out of alpha. For now, it's installable with `pip install -i https://test.pypi.org/simple/ mantaray`, which just pulls from the PyPI testing registry.

## Examples
Examples can be found under `examples/`. These target the [Nexys4 DDR](https://digilent.com/reference/programmable-logic/nexys-4-ddr/start) and [Nexys A7-100T](https://digilent.com/reference/programmable-logic/nexys-a7/start) from Digilent, which are functionally equivalent.

## About
Manta was originally developed as part of my [Master's Thesis at MIT](dspace.mit.edu) in 2023, done under the supervision of Joe Steinmeyer. But I think it's a neat tool, so I'm still working on it :)