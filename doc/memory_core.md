
## Overview

Memory is used to store data when the space needed exceeds a few registers. As a result, Manta provides a Memory core, which instantiates a dual-port RAM on the FPGA. One port is provided to the host, and the other is connected to your logic with a simple `addr`/`data_in`/`data_out`/`write_enable` interface. This allows the host machine to exchange larger amounts of data with your logic on the FPGA.

This is a very, very simple task - however it's surprisingly useful in practice. Both the [Use Cases](../use_cases) page and the repository's [examples](https://github.com/fischermoseley/manta/tree/main/examples) folder contain examples of the Memory Core for your reference.

Manta won't impose any limit on the width or depth of the memory you instantiate, but you will be limited by the available resources and timing properties of your FPGA.

!!! warning "Words update 16 bits at a time!"

    Due to the structure of Manta's internal bus, the Memory core only updates 16 bits of a word at a time. For instance, writing a new value to a 33-bit wide memory would update bits 0-15 on one clock cycle, bits 16-31 on another, and bit 32 on another still. Manta makes no guarantees about the time taken between each of these updates. If this is a problem for your application, consider using an IO Core as a doorbell to signal when the memory is valid, or ping-pong between two Memory Cores.


## On-Chip Implementation

Manta will make a best-effort attempt to implement the memory in Block RAM, if it is available on the device. This is done by exporting Verilog that synthesis tools should infer as Block RAMs, however this inference is not guaranteed. Depending on your toolchain and the FPGA's architecture, the Verilog produced by Manta may be implemented as FF RAM, LUT (Distributed) RAM, or something else. These memory types are well explained in the [Yosys documentation](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/synthesis/memory.html), but be sure to check your toolchain's documentation as well.

## Configuration

As explained in the [getting started](../getting_started) page, the Memory Core must be configured and included in the FPGA design before it can be operated. Configuration is performed differently depending on if you're using a traditional Verilog-based workflow, or if you're building an Amaranth-native design.

### Verilog-Based Workflows

The Memory Core is used by adding an entry in a `cores` section of a configuration file. This is best shown by example:

```yaml
---
cores:
  my_memory:
    type: memory
    mode: bidirectional
    width: 12
    depth: 16384

```

Inside this configuration, the following parameters may be set:

- `name`: The name of the Memory core, which is used when working with the API.
- `type`: This denotes that this is a Memory core. All cores contain a `type` field, which must be set to `memory` to be recognized as an Memory core.
- `mode`: The mode for the Memory core to operate in. This must be one of `bidirectional`, `host_to_fpga`, or `fpga_to_host`. Bidirectional memories can be both read or written to by the host and FPGA, but they require the use of a True Dual Port RAM, which is not available on all platforms (most notably, the ice40). Host-to-fpga and fpga-to-host RAMs only require a Simple Dual Port RAM, which is available on nearly all platforms.
- `width`: The width of the Memory core, in bits.
- `depth`: The depth of the Memory core, in entries.

### Amaranth-Native Designs

Since Amaranth modules are Python objects, the configuration of the Memory Core is given by the arguments given during initialization. See the documentation for the `MemoryCore` [class constructor](#manta.MemoryCore) below, as well as the Amaranth [examples](https://github.com/fischermoseley/manta/tree/main/examples/amaranth) in the repo.


## Operation

Regardless of the technique you used to configure your Memory Core, it is operated using the [`read()`](#manta.MemoryCore.read) and [`write()`](#manta.MemoryCore.write) methods. Documentation for these methods is available below.

These methods are members of the `MemoryCore` class, so if you're using Manta in a Verilog-based workflow, you'll first need to obtain a `Manta` object that contains an `MemoryCore` member. This is done with `Manta.from_config()`, as shown in the Verilog [examples](https://github.com/fischermoseley/manta/tree/main/examples/verilog).


## Python API Documentation

::: manta.MemoryCore
