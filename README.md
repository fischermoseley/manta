![](doc/assets/logo.png)

## Manta: A Configurable and Approachable Tool for FPGA Debugging and Rapid Prototyping
![functional_simulation](https://github.com/fischermoseley/manta/actions/workflows/functional_simulation.yml/badge.svg)
![formal_verification](https://github.com/fischermoseley/manta/actions/workflows/formal_verification.yml/badge.svg)
![build_examples](https://github.com/fischermoseley/manta/actions/workflows/build_examples.yml/badge.svg)
![build_docs](https://github.com/fischermoseley/manta/actions/workflows/build_docs.yml/badge.svg)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Manta is a tool for getting information into and out of FPGAs over an interface like UART or Ethernet. It's primarily intended for debugging, but it's robust enough to be a simple, reliable transport layer between a FPGA and a host machine. It lets you configure a series of cores on a shared bus via a YAML or JSON file, and then provides a Python API to each core, along with vendor-agnostic Verilog HDL to instantiate them on your FPGA.

For more information check out the docs:
[https://fischermoseley.github.io/manta](https://fischermoseley.github.io/manta)
