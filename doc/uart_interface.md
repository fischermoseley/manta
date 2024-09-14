## Overview

The ubiquity and simplicity of UART makes it a convenient mechanism for sharing data between the host machine and FPGA. As a result, Manta provides the option to run over UART, where operating the cores can often take place over the same USB cable used to program the FPGA.

Both the [Use Cases](../use_cases) page and the repository's [examples](https://github.com/fischermoseley/manta/tree/main/examples) folder contain examples of the UART Interface for your reference.

## Configuration

### Verilog-Based Workflows

The UART interface is used by adding a `uart` entry at the bottom of the configuration file. This is best shown by example:

```yaml
uart:
  port: "auto"
  baudrate: 3000000
  clock_freq: 100000000
  stall_interval: 16
  chunk_size: 256
```
Inside this configuration, the following parameters may be set:

- `port` _(required)_: The name of the serial port on the host machine that's connected to the FPGA. Depending on your platform, this could be `/dev/ttyUSBXX`, `/dev/tty.usbserialXXX`, or `COMX`. If set to `auto`, then Manta will try to find the right serial port by looking for a connected FTDI chip. This doesn't always work, so if your port isn't automatically detected then just specify the port manually.

- `baudrate` _(required)_: The baudrate of the serial port. Generally, this should be set to the maximum baudrate supported by the USB/UART chip on your dev board for fastest operation. Manta will throw an error if this baudrate is not achievable with your FPGA's clock frequency.

- `clock_freq` _(required)_: The frequency of the clock provided to the `manta` module, in Hertz (Hz). This is used to calculate an appropriate prescaler onboard the FPGA to acheive the desired baudrate. Manta will throw an error if this clock frequency does not allow you to achieve your desired baudrate.

- `stall_interval` _(optional)_: The number of read requests to send before sending a stall byte. This prevents packets from being dropped if the FPGA's baudrate is less than the USB-Serial adapter's baudrate. This is usually caused by a mismatch between the clock frequency of the USB-Serial adapter and the FPGA fabric. See issue [#18](https://github.com/fischermoseley/manta/issues/18) on GitHub. Defaults to 16, reduce this if Manta reports that bytes are being dropped.

- `chunk_size` _(optional)_: The number of read requests to send at a time. Since the FPGA responds to read requests almost instantly, sending them in batches prevents the host machine's input buffer from overflowing. Defaults to 256, Reduce this if Manta reports that bytes are being dropped, and decreasing `stall_interval` did not work.

### Amaranth-Native Designs

Since Amaranth modules are Python objects, the configuration of the IO Core is given by the arguments given during initialization. See the documentation for the `UARTInterface` [class constructor](#manta.UARTInterface) below, as well as the Amaranth [examples](https://github.com/fischermoseley/manta/tree/main/examples/amaranth) in the repo.

::: manta.UARTInterface
    options:
      members: false