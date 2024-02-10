## Overview
For scenarios where UART is not available or higher bandwidth is desired, Manta provides an Ethernet interface for communicating between the host and FPGA. This interface uses UDP for communication, and leverages the builtin Python `sockets` module on the host side, and the open-source [LiteEth](https://github.com/enjoy-digital/liteeth) Ethernet core on the FPGA side.

!!! warning "Not every device is supported!"

    Although Manta aims to be as platform-agnostic as possible, Ethernet PHYs and FPGA clock primitives are very particular devices. As a result, the supported devices are loosely restricted to those on [this list](https://github.com/enjoy-digital/liteeth?tab=readme-ov-file#-features). If a device you'd like to use isn't on the list, the community would love your help!

Although UDP does not guarantee reliable packet delivery, this usually doesn't pose an issue in practice. Manta will throw a runtime error if packets are dropped, and the UDP checksum and Ethernet FCS guarantee that any data delivered is not corrupted. Together, these two behaviors prevent corrupted data from being provided to the user, as Manta will error before returning invalid data. As long as your network is not terribly congested, Manta will operate without issue.

## Configuration

The configuration of the Ethernet core is best shown by example:
```yaml
ethernet:
  phy: LiteEthPHYRMII
  vendor: xilinx
  toolchain: vivado

  clk_freq: 50e6
  refclk_freq: 50e6

  fpga_ip_addr: "192.168.0.110"
  host_ip_addr: "192.168.0.100"
```
This snippet at the end of the configuration file defines the interface. The following parameters must be set:

- `phy` _(required)_: The name of the LiteEth PHY class to use. Valid values consist of any of the names in [this list](https://github.com/enjoy-digital/liteeth/blob/b4e28506238c5340f2ade7899c2223424cabd410/liteeth/phy/__init__.py#L25-L45). Select the appropriate one for your FPGA vendor and family.

- `vendor` _(required)_: The vendor of the FPGA being designed for. Currently only values of `xilinx` and `lattice` are supported. Used to generate timing constraints files, which are currently unused.

- `toolchain` _(required)_: The toolchain being used. Currently only values of `vivado` and `diamond` are supported.

- `clk_freq` _(required)_: The frequency of the clock provided to the Manta instance. Used to configure a PLL in the FPGA fabric for generating the PHY's `refclk`.

- `refclk_freq` _(required)_: The frequency of the reference clock to be provided to the Ethernet PHY. This clock is generated from Manta's main clock using a PLL inside the FPGA. This frequency must match the MII variant supported by the PHY, as well as speed that the PHY is being operated at. For instance, a RGMII PHY may be operated at either 125MHz in Gigabit mode, or 25MHz in 100Mbps mode.

- `fpga_ip_addr` _(required)_: The IP address the FPGA will attempt to claim. Upon power-on, the FPGA will issue a DHCP request for this IP address. The easiest way to check if this was successful is by pinging the FPGA's IP, but if you have access to your network's router it may report a list of connected devices.

- `host_ip_addr` _(required)_: The IP address of the host machine, which the FPGA will send packets back to.
