![](doc/assets/manta.png)

## Manta: An In-Situ Debugging Tool for Programmable Hardware
![functional_simulation](https://github.com/fischermoseley/manta/actions/workflows/functional_simulation.yml/badge.svg)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manta is a tool for debugging FPGA designs over an interface like UART or Ethernet. It works by allowing the user to instantiate a number of debug cores in a design, and exposes a Python interface to them. This permits rapid prototyping of logic in Python, and a means of incrementally migrating it to HDL. The cores are described below.

Manta is written in Python, and generates Verilog-2001 HDL. It's cross-platform, and its only dependencies are pySerial and pyYAML.

For more information check out the docs at [https://fischermoseley.github.io/manta](https://fischermoseley.github.io/manta)