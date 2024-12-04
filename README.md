![](https://raw.githubusercontent.com/fischermoseley/manta/refs/heads/main/doc/assets/logo.png)

## Manta: A Configurable and Approachable Tool for FPGA Debugging and Rapid Prototyping
![run_tests](https://github.com/fischermoseley/manta/actions/workflows/run_tests.yml/badge.svg)
![build_docs](https://github.com/fischermoseley/manta/actions/workflows/build_docs.yml/badge.svg)
[![codecov](https://codecov.io/gh/fischermoseley/manta/graph/badge.svg?token=1GGHCICK3Q)](https://codecov.io/gh/fischermoseley/manta)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Manta is a tool for getting information into and out of FPGAs over an interface like UART or Ethernet. It's primarily intended for debugging, but it's robust enough to be a simple, reliable transport layer between a FPGA and a host machine. It lets you configure a series of cores on a shared bus via a YAML or JSON file, and then provides a Python API to each core, along with vendor-agnostic Verilog HDL to instantiate them on your FPGA.

For more information check out the docs:
[https://fischermoseley.github.io/manta](https://fischermoseley.github.io/manta)
