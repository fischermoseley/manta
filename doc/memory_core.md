
## Overview
Memory is the de facto means of storing data on FPGAs when the space needed exceeds a few registers. As a result, Manta provides a Memory core, which instantiates a dual-port RAM on the FPGA. One port is provided to the host, and the other is connected to your logic with the standard RAM interface (`addr`, `data_in`, `data_out`, `write_enable`). This allows the host to provide reasonably large amounts of data to user logic - or the other way around, or a mix of both!

This is a very, very simple task - and while configuration is straightforward, there are a few caveats. More on both topics below:

## Configuration

Just like the rest of the cores, the Memory core is configured via an entry in a project's configuration file. This is easiest to show by example:

```yaml
---
cores:
  my_memory:
    type: memory
    mode: bidirectional
    width: 12
    depth: 16384

```

There's a few parameters that get configured here, including:

- `name`: The name of the Memory core. This name is used to reference the core when working with the API, and can be whatever you'd like.
- `type`: This denotes that this is a Memory core. All cores contain a `type` field, which must be set to `memory` to be recognized as an Memory core.
- `mode`: The mode for the Memory core to operate in. This must be one of `bidirectional`, `host_to_fpga`, or `fpga_to_host`. Bidirectional memories can be both read or written to by the host and FPGA, but they require the use of a True Dual Port RAM, which is not available on all platforms (most notably, the ice40). Host-to-fpga and fpga-to-host RAMs only require a Simple Dual Port RAM, which is available on nearly all platforms.
- `width`: The width of the Memory core, in bits.
- `depth`: The depth of the Memory core, in entries.

Manta won't impose any limit on the width or depth of the memory you instantiate, but since Manta instantiates BRAM primitives on the FPGA, you will be limited by what your FPGA can support. It helps to know your particular FPGA's architecture here.

### On-Chip Implementation

For most use cases, Manta will choose to implement the memory in Block RAM, if it is available on the device. However, the Verilog produced by Manta may be inferred to a number of memory types, including FF RAM or LUT (Distributed) RAM. For more information on how this is chosen, please refer to the [Yosys documentation](https://yosyshq.readthedocs.io/projects/yosys/en/latest/CHAPTER_Memorymap.html).

### Python API

The Memory core functionality is stored in the `Manta.MemoryCore` classes in [src/manta/memory_core.py](https://github.com/fischermoseley/manta/blob/main/src/manta/memory_core.py), and it may be controlled with the two functions:

Just like with the other cores, interfacing with the Memory with the Python API is simple:

```python
from manta import Manta
m = manta('manta.yaml')

m.my_memory.write(addr=38, data=600)
m.my_memory.write(addr=0x1234, data = 0b100011101011)
m.my_memory.write(0x0612, 0x2001)

foo = m.my_memory.write(addr=38)
foo = m.my_memory.write(addr=1234)
foo = m.my_memory.write(0x0612)
```

Reading/writing in batches is also supported. This is recommended where possible, as reads are massively sped up by performing them in bulk:

```python
addrs = list(range(0, 1234))
datas = list(range(1234, 2468))
m.my_memory.write(addrs, datas)

foo = m.my_memory.read(addrs)
```

### Synchronicity

Since Manta's [data bus](architecture.md#data-bus) is only 16-bits wide, it's only possible to manipulate the Memory core in 16-bit increments. This means that if you have a RAM that's ≤16 bits wide, you'll only need to issue a single bus transaction to read/write one entry in the RAM. However, if you have a RAM that's ≥16 bits wide, you'll need to issue a bus transaction to update each 16-bit slice of it. For instance, updating a single entry in a 33-bit wide RAM would require sending 3 messages to the FPGA: one for bits 1-16, another for bits 17-32, and one for bit 33. If your application expects each RAM entry to update instantaneously, this could be problematic.

There's a few different ways to solve this - you could use an IO core to signal when a RAM's contents or valid - or you could ping-pong between two RAMs while one is being modified. The choice is yours, and Manta makes no attempt to prescribe any particular approach.

Lastly, the interface you use (and to a lesser extent, your operating system) will determine the space between bus transactions. For instance, 100Mbit Ethernet is a thousand times faster than 115200bps UART, so the time where the RAM is invalid is a thousand times smaller.
