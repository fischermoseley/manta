## Overview

For applications where UART is too slow or isn't available, Manta provides the option to run over Ethernet. This is done via UDP, so the FPGA can be anywhere on the same network as the host machine - as opposed to MAC-based Ethernet interfaces, which usually require a point-to-point network connection between the FPGA and the host. Although UDP does not guaruntee reliable, in-order packet delivery, this generally tends to be the case on uncongested networks. In the future, Manta will enforce this at the [application layer](https://github.com/fischermoseley/manta/issues/10).

!!! info "Not every device is supported!"

    Internally, the Ethernet Interface uses [LiteEth](https://github.com/enjoy-digital/liteeth) to generate cross-platform RTL for the FPGA. As a result, the supported devices are loosely restricted to those [supported by LiteEth](https://github.com/enjoy-digital/liteeth?tab=readme-ov-file#-features). If a device you'd like to use isn't on the list, the community would love your help.


Both the [Use Cases](../use_cases) page and the repository's [examples](https://github.com/fischermoseley/manta/tree/main/examples) folder contain examples of the Ethernet Interface for your reference.


## Configuration

### Verilog-Based Workflows

The UART interface is used by adding a `ethernet` entry at the bottom of the configuration file. This is best shown by example:

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
Inside this configuration, the following parameters may be set:

- `phy` _(required)_: The name of the LiteEth PHY class to use. Select the appropriate one from [this list](https://github.com/enjoy-digital/liteeth/blob/b4e28506238c5340f2ade7899c2223424cabd410/liteeth/phy/__init__.py#L25-L45) for your FPGA vendor and family.

- `vendor` _(required)_: The vendor of your FPGA. Currently only values of `xilinx` and `lattice` are supported. This is used to generate (currently unused) timing constraints files.

- `toolchain` _(required)_: The toolchain being used. Currently only values of `vivado` and `diamond` are supported.

- `clk_freq` _(required)_: The frequency of the clock provided to the Manta module on the FPGA, in Hertz (Hz).

- `refclk_freq` _(required)_: The frequency of the reference clock to be provided to the Ethernet PHY, in Hertz (Hz). This frequency must match the MII variant used by the PHY, and speed it is being operated at. For instance, a RGMII PHY may be operated at either 125MHz in Gigabit mode, or 25MHz in 100Mbps mode.

- `fpga_ip_addr` _(required)_: The IP address the FPGA will attempt to claim. Upon power-on, the FPGA will issue a DHCP request for this IP address. Ping this address after power-on to check if this request was successful, or check your router for a list of connected devices.

- `host_ip_addr` _(required)_: The IP address of the host machine, which the FPGA will send packets back to.

- `udp_port` _(optional)_: The UDP port to communicate over. Defaults to 2001.

Lastly, any additonal arguments provided in the `ethernet` section of the config file will be passed to the LiteEth standalone core generator. As a result, the [examples](https://github.com/enjoy-digital/liteeth/tree/master/examples) provided by LiteEth may be of some service to you if you're bringing up a different FPGA!

!!! warning "LiteEth doesn't always generate its own `refclk`!"

    Although LitEth is built on Migen and LiteX which support PLLs and other clock generation primitives, I haven't seen it instantiate one to synthesize a suitable `refclk` at the appropriate frequency from the input clock. As a result, for now it's recommended to generate your `refclk` outside Manta, and then use it to clock your Manta instance.

### Amaranth-Native Designs

Since Amaranth modules are Python objects, the configuration of the IO Core is given by the arguments given during initialization. See the documentation for the `EthernetInterface` [class constructor](#manta.EthernetInterface) below, as well as the Amaranth [examples](https://github.com/fischermoseley/manta/tree/main/examples/amaranth) in the repo.

::: manta.EthernetInterface
    options:
      members: false