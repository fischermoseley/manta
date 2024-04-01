
## Overview

To use Manta, you'll need a host machine with a FPGA board connected over UART, or a FPGA board connected to the same network via Ethernet. You'll then:

- _Specify a set of debug cores you wish to include in your design._ This is done by writing a configuration file, typically called `manta.yaml`. Specifying files in JSON is also supported, as long as the hierarchy in the file is equivalent. Just make sure that your YAML files end in `.yaml` or `.yml`, and that JSON files end in `.json`.
- _Invoke Manta to generate Verilog from the configuration provided._ This is done by running `manta gen [config_file] [verilog_file]` at the command line, which generates a Verilog file (typically named `manta.v`) from the provided configuration file. This Verilog file contains a definition for a Verilog module named `manta`, and all its constituent modules.
- _Instantiate `manta` in your design, and connecting it to the logic you'd like to debug._ Manta will provide an example instantiation if you run `manta inst [config_file]`, which you can copy-paste into your source code. You'll connect its ports to the logic you're trying to debug, as well as to whatever interface you're using to communicate with the host. This will be a serial transciever on your development board if you're using UART, or it's RMII PHY if you're using Ethernet.
- _Build and upload the design to your FPGA using your preferred toolchain._
- _Use the debug core(s) through the Python API or the command line._ The functions availble to each core are described in their documentation.
- _Repeat!_ As you debug, you'll probably want to change exactly how Manta is configured. This means tweaking the configuration file, regenerating the Verilog module, and so on.

## Example Configuration

An example config file is provided below. If this file was named `manta.yaml` then running `manta gen manta.yaml manta.v` would generate Verilog for a `manta` module that matched the config file.

```yaml
---
cores:
  my_io_core:
    type: io

    inputs:
      probe_0_in: 6
      probe_1_in: 12

    outputs:
      probe_2_out: 20
      probe_3_out: 1

  my_logic_analyzer:
    type: logic_analyzer
    sample_depth: 4096
    trigger_location: 1000

    probes:
      larry: 1
      curly: 3
      moe: 9

    triggers:
      - moe RISING
      - curly FALLING

uart:
  port: "auto"
  baudrate: 3000000
  clock_freq: 100000000
```

Although it's just an example, this config file shows the two things every Manta configuration needs, namely:

- ___Cores___: A list of the debug cores Manta should place on your FPGA. The behavior and configuration of the cores is described in more detail on their documentation pages, but this list contains each core you'd like included in your `manta` module. This list can have as many entires as your FPGA can support, so long as Manta can address them all. If it can't, it'll throw an error when it tries to generate Verilog.

- ___Interface___: The way data gets on and off the FPGA. At present, Manta only supports UART and Ethernet interfaces. These are described in more detail on their documentation pages, but the interface of choice is specified with either a `uart` or `ethernet` at the end of the configuration file.

This Manta instance has an IO Core and a Logic Analyzer, each containing a number of probes at variable widths. The Manta module itself is provided a 100MHz clock, and communicates with the host over UART running at 3Mbaud. This is just an example, and more details are available in the documentation page for each core.

## Example Instantiation

Lastly, we Manta can automatically generate a copy-pasteable Verilog snippet to instantiate Manta in your design by running `manta inst [config_file]`. For example, the following snippet is generated for the configuration above:

> Note: The reset signal, `rst`, is an active HIGH signal.

```verilog
manta manta_inst (
    .clk(clk),
    .rst(rst),
    .rx(rx),
    .tx(tx),
    .probe_0_in(probe_0_in),
    .probe_1_in(probe_1_in),
    .probe_2_out(probe_2_out),
    .probe_3_out(probe_3_out),
    .larry(larry),
    .curly(curly),
    .moe(moe));
```
