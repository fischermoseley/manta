![](assets/manta.png)

<div align="center">
  An In-Situ Debugging Tool for Programmable Hardware
</div>

Manta is a tool for debugging FPGA designs over UART. It has two modes for doing this, downlink and uplink. The downlink mode feels similar to a logic analyzer, in that Manta provides a waveform view of a configurable set of signals, which get captured when some trigger condition is met. The uplink mode allows a host machine to remotely set values of registers on the FPGA via a python interface. This permits rapid prototyping of logic in Python, and a means of incrementally migrating it to HDL. A more detailed description of each mode is below.

Manta is written in Python, and generates SystemVerilog HDL. It's cross-platform, and its only dependency is pySerial. The SystemVerilog templates are included in the Python source, so only a single python file must be included in your project.

## Downlink

Manta's downlink mode works by taking a JSON file describing the ILA configuration, and autogenerating a debug core with SystemVerilog. This gets included in the rest of the project's HDL, and is synthesized and flashed on the FPGA. It can then be controlled by a host machine connected over a serial port. The host can arm the core, and then when a trigger condition is met, the debug output is wired back to the host, where it's saved as a waveform file. This can then be opened and inspected in a waveform viewer like GTKWave.

This is similar to Xilinx's Integrated Logic Analyzer (ILA) and Intel/Altera's SignalTap utility.

## Uplink:


## Getting Started

Since Manta is designed to be both cross-platform and unintrusive to your project source, it's packaged as a single python file with the HDL templates built in. This isn't the cleanest thing to develop with, so it's developed as a set of files that are stitched together into a single Python script. This isn't compilation since we're not going to machine code - we're just building a script, not a binary.

### Using a prebuilt script

Copy `ila.py` into the root of your project directory. Also copy a configuration template (`config_template.yml` or `config_template.json`) if you wish.

### Building from source

Clone the repo, and then run `build.py`. This will output an `ila.py`, which you're free to use.

## Examples
Examples can be found under `examples/`.

## About 
Manta was originally developed as part of my Master's Thesis at MIT in 2023, done under the supervision of Joe Steinmeyer. But I think it's a neat tool, so I'm still working on it :)
