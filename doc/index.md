![](assets/logo.png)

## Manta: A Configurable and Approachable Tool for FPGA Debugging and Rapid Prototyping

Manta is a tool for rapidly prototyping and debugging FPGA designs. It works by providing a Manta module which is included in a FPGA design, which itself contains a number of *cores* - small, configurable debugging blocks that each provide some functionality. These cores are then connected to your design, and allow you to interface with it from a connected host machine.

These cores include functionality such as register reads/writes, memory accesses, and an embedded logic analyzer. Manta includes both a UART and Ethernet (via UDP) interface for communication between the host and FPGA.

Manta specifies its RTL logic with [Amaranth](https://github.com/amaranth-lang/amaranth) which allows it to target nearly any FPGA device, regardless of vendor. Manta itself is written in pure Python, which allows it to run on Windows, macOS, Linux, and BSD across a variety of CPU architectures. Manta can be included natively in Amaranth-based designs, or export Verilog-2001 for use in traditional Verilog-based workflows.

## About
Manta and its source code are released under a [GPLv3 license](https://github.com/fischermoseley/manta/blob/main/LICENSE.txt), and it was originally developed as part of my [Master's Thesis at MIT](https://hdl.handle.net/1721.1/151223) in 2023, done under the supervision of [Dr. Joe Steinmeyer](https://www.jodalyst.com/). The following Bibtex is available if you wish to cite it:

```bibtex
@misc{manta2023,
    author={Fischer Moseley},
    title={Manta: An In-Situ Debugging Tool for Programmable Hardware},
    year={2023},
    month={may}
    howpublished={\url{https://hdl.handle.net/1721.1/151223}}
}
```
