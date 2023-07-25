You'll need a working installation of Manta, which you can get by following the [installation instructions](./installation.md). You'll also likely want a copy of the GitHub repo, which contains the code for this tutorial in the `examples/` folder.

This tutorial configures Manta with an __IO Core__, which creates a `manta` module in Verilog that exposes a set of registers. These registers connect to your HDL, and each may be configured as either an input or an output. This module is configured from a YAML file, which looks like this:

```yaml
---
cores:
  my_io_core:
    type: io

    inputs:
      spike: 1
      jet: 12
      valentine: 6
      ed: 9
      ein: 16

    outputs:
      shepherd: 10
      wrex: 1
      tali: 5
      garrus: 3

uart:
  port: "auto"
  baudrate: 115200
  clock_freq: 100000000
```

There's two things going on in this file. First, we've added an IO core to our Manta module, and named it `my_io_core`. We've also specified what registers we'd like it to expose, and provided names and bit widths for each. Feel free to name these however you'd like, but for simplicity it's usually best to give them the same name as what they connect to in your code. If you'd like to know more about what the IO core can do, check out it's [docs](./io_core.md).

Second, this file specifies that we'll be using UART to communicate between the host machine and the FPGA. We've asked Manta to try and find which serial port on the host machine is connected to the serial port by specifying `port: "auto"`, but if this doesn't work you can specify `"COM1"`, "/dev/ttyUSB0", or whatever descriptor your operating system gives it. Because of the way UART works, the baudrate must be set beforehand, and Manta needs to know how fast the FPGA clock is so that it can match it on the FPGA. If you'd like to more about the UART interface, check out the [docs](./uart.md)!

It's worth noting that we could also add more cores to our Manta configuration. Depending on your applicaition, a [Logic Analyzer](./logic_analyzer_core.md) core or [Block Memory](./block_memory_core.md) core might be useful! Manta supports any amount of any cores, so ou could even add another IO core (although you might want to consider just expanding your existing one!)

The snippet shown above is just an example, and our actual configuration is in the `examples/` folder of the GitHub repo. Feel free to grab either the UART or Ethernet variant - the only difference is the interface used. Both variants create a Manta instance with an IO core, where the onboard switches and buttons are wired as inputs, and the LEDs are connected as outputs.

Once the configuration has been specified, we'll need to generate the Verilog source for the module we'd like to instantiate on the FPGA. This is done by:

`manta gen <path_to_config_file> <path_to_output_verilog>`

In the case of the example code in the GitHub repo is:

`manta gen manta.yaml src/manta.v`

Go ahead and have a look at the Verilog file it just spat out - it contains a definition for a module called `manta`, which we'll instantiate in our design. There's also a copy-and-pasteable module instantiation at the top of the generated Verilog file. The GitHub example does this in the top-level module, where it wires the IO core to the Nexys A7's onboard IO.

Feel free to build this however you'd like - we like running Vivado in batch mode with the provided build script, which you can do with `vivado -mode batch -source build.tcl`. Upload the generated bitstream to your board.

### Using the Python API

Now that Manta's on the FPGA, we can control the IO core from our host machine. Using the API looks about like the following:

```python
from manta import Manta
m = Manta('manta.yaml')
m.my_io_core.led.set(1)

print(my_io_core.btnc.get())
```

This creates a Manta object from the same configuration file we used earlier, which contains all of the cores we specified. In this case it's just the single IO core, which can have its outputs registers written to (and input registers read from) with the methods above. The [`examples/api_example.py`](https://github.com/fischermoseley/manta/tree/main/examples/nexys_a7/io_core_uart/api_example.py) script uses this to display a pattern on the onboard LEDs, and report the status of the onboard buttons and switches.

This is just a quick example! More details about the IO core can be found on [its page](./io_core.md).