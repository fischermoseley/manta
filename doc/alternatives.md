There's quite a few FPGA debugging tools out there, and it may happen that your needs are better met by another tool. This section aims to provide a list of alternatives, in hopes that you're able to be confident in your debugging flow.

## Open Source Tools

### LiteScope

An embedded logic analyzer written in Migen, primarily for use in LiteX SoC designs. Also includes IO peek and poke, as well as UART, Ethernet, and PCIe interfaces with a host machine. Includes VCD, Sigrok, CSV, and Python data export.

- [Source Code](https://github.com/enjoy-digital/litescope)
- [Documentation](https://github.com/enjoy-digital/litex/wiki/Use-LiteScope-To-Debug-A-SoC)

### ZipCPU Debugger

A set of embedded debugging modules written by Dan Gisselquist of ZipCPU fame. Communication between the host and FPGA is accomplished with UART, and control of the debugger is performed with a C++ API on the host. A wishbone interface is provided on the FPGA side to connect to other Wishbone-based debugging tools that can provide control of user registers, block RAM, and an embedded logic analyzer. Supports dumping of signals to a VCD file.

- [Source Code](https://github.com/ZipCPU/dbgbus)
- [Documentation](https://zipcpu.com/topics.html), under the _How to Debug an FPGA_ section.

## Commercial Tools

### Xilinx Integrated Logic Analzyer

An embedded logic analyzer for Xilinx FPGAs, provided as part of the Xilinx Vivado development suite. Communication between the host and FPGA is accomplished with JTAG, typically running over a USB cable to the device. Includes an integrated waveform viewer, and VCD and CSV export. Also supports a JTAG-to-AXI mode, which integrates well with Xilinx IP, which uses primarily AXI. Also integrates with the ChipScoPy API, which allows for Python control of the ILA on Versal devices. The ILA was previously known as ChipScope in earlier versions of Vivado.

- [ILA Documentation](https://docs.xilinx.com/v/u/en-US/pg172-ila)
- [ILA User's Guide](https://docs.xilinx.com/r/en-US/ug936-vivado-tutorial-programming-debugging/Using-the-Vivado-Logic-Analyzer-to-Debug-Hardware)
- [ChipScoPy API](https://github.com/Xilinx/chipscopy)


### Xilinx Virtual IO

A tool for reading and writing to individual registers on the FPGA, provided as part of the Xilinx Vivado development suite. Just like the ILA, communication between the host and FPGA is done over JTAG. Control over the registers is done through the Vivado GUI or through the Tcl interpreter. In the case of Versal devices, the ChipScoPy API can also control the registers.

- [Virtual IO Documentation](https://docs.xilinx.com/v/u/en-US/pg159-vio)
- [ChipScoPy API](https://github.com/Xilinx/chipscopy)

### Intel Signal Tap

An embedded logic analyzer for Intel/Altera FPGAs, provided as part of the Quartus development suite. Communication between the host and FPGA is accomplished with JTAG, and a programmable interface is provided via Tcl. Signal Tap is notable for providing a significant amount of configurability in the trigger conditions, and provides a small scripting language called _Trigger Flow_ that allows users to define triggers as state machines. Signal Tap also allows for _Simulation-Aware nodes_, which allows for running simulations with data captured from the real world. At the time of writing, this feature is only available in the most recent and full-featured version of the Quartus suite, Quartus Prime Pro Edition 22.4.

- [Documentation](https://www.intel.com/content/www/us/en/docs/programmable/683552/18-1/design-debugging-with-the-logic-analyzer-69524.html)


### Intel In-System Sources and Probes

A tool for reading and writing to individual registers on the FPGA, provided for Intel/Altera FPGAs as part of the Quartus development suite. Just like Signal Tap, communication between the host and FPGA is accomplished with JTAG.

- [Documentation](https://www.intel.com/content/www/us/en/docs/programmable/683552/18-1/design-debugging-using-in-system-sources-45607.html)

### Lattice Reveal

An embedded logic analyzer for Lattice FPGAs, provided as part of the Diamond development suite. Communication between the host and FPGA is accomplished with JTAG. Reveal is notable for providing a significant amount of configurability in the trigger conditions, and supports trigger conditions formed with a mix of combinational and sequential logic. Reveal also provides special support for Wishbone buses, and for controlling SERDES modules on ECP5 devices.

- [Documentation](https://www.latticesemi.com/~/media/328D471BF2C74EB1907832FAA6FB344B.ashx)

### Opal Kelly FrontPanel SDK

Unlike other entries in this list, Opal Kelly's FrontPanel SDK is not marketed as a debugger (although it can be used as such). Instead, it's designed to provide a host computer with a real time interface to FGPA signals, and present them on a graphical “front panel". These front panels exist as a GUI window on the host, and contain buttons, knobs, and indicators, much like a LabVIEW virtual instrument. Communication between the host and FPGA is accomplished with either USB or PCIe. Bindings for hosts running Windows, macOS, and Linux are provided, and target C, C++, C#, Python, Java, Ruby, and MATLAB. The FrontPanel SDK differs from other debuggers in that it provides a skeleton module into which the user logic is instantiated, instead of being instantiated inside the user's logic.

- [Documentation](https://docs.opalkelly.com/fpsdk/)
- [User's Guide](https://assets00.opalkelly.com/library/FrontPanel-UM.pdf)