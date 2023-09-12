## Overview

Manta needs an interface to pass data between the host machine and FPGA, and UART is a convenient option. When configured to use UART, Manta will shuffle data back and forth using generic 8N1 serial with no flow control. This happens through a series of read and write transactions, which are specified using a messaging format described [here](../how_it_works/#message-format).

## Configuration

The configuration of the UART interface is best shown by example:

```yaml
uart:
  port: "auto"
  baudrate: 3000000
  clock_freq: 100000000
```
This snippet defines the interface, and lives at the bottom of a Manta configuration file. Three parameters must be set:

- `port` _(required)_: The name of the serial port on the host machine that's connected to the FPGA. Depending on your platform, this could be `/dev/ttyUSBXX`, `/dev/tty.usbserialXXX`, or `COMX`. If set to `auto`, then Manta will try to find the right serial port by looking for a USB device with the same VID and PID as a FT2232 - a USB/UART converter chip that's super popular on FPGA dev boards. This doesn't always work, but it's super convenient when it does. If your port isn't automatically detected, then just specify the port manually.

- `baudrate` _(required)_: The baudrate of the serial port. Generally you want to configure this at the maximum speed of your USB/UART chip such that data transfers as fast as possible. The ubiquitous FT2232 supports up to 3Mbaud.

- `clock_freq` _(required)_: The frequency of the clock being provided to the `manta` module, in Hertz (Hz). This speed doesn't matter much to the logic itself, it's only used to calculate the correct baud timing for the provided baudrate. However, this frequency does have to be fast enough to ensure a good agreement between the onboard prescaler and the requested baudrate - and Manta will throw an error during code generation if that is not the case.
