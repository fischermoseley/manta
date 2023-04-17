
## Usage


### Configuration
The block memory core can be included in your configuration just like any other core. Only the `width` and `depth` parameters are needed:

```yaml
---
cores:
  my_block_memory:
    type: block_memory
    width: 12 # (1)
    depth: 16384

```

1. If your BRAM is more than 16 bits wide, check out the section on [Synchronicity](#synchronicity) and make sure Manta's behavior is compatible with your project.

### Verilog
Internally this creates a dual-port BRAM, connects one end to Manta's internal bus, and exposes the other to the user:

```systemverilog
manta manta_inst (
    .clk(clk),

    .rx(rx),
    .tx(tx),

    .my_block_memory_clk(),
    .my_block_memory_addr(),
    .my_block_memory_din(),
    .my_block_memory_dout(),
    .my_block_memory_we());
```

Which are free to connect to whatever logic the user desires.

### Python
Just like with the other cores, interfacing with the BRAM with the Python API is simple:

```python
from manta import Manta
m = manta('manta.yaml')

m.my_block_memory.write(addr=38, data=600)
m.my_block_memory.write(addr=0x1234, data = 0b100011101011)
m.my_block_memory.write(0x0612, 0x2001)

foo = m.my_block_memory.write(addr=38)
foo = m.my_block_memory.write(addr=1234)
foo = m.my_block_memory.write(0x0612)
```

Reading/writing in batches is also supported. This is recommended where possible, as reads are massively sped up by performing them in bulk:

```python
addrs = list(range(0, 1234))
datas = list(range(1234, 2468))
m.my_block_memory.write(addrs, datas)

foo = m.my_block_memory.read(addrs)
```

### Examples

A Block Memory core is used in the [video_sprite](https://github.com/fischermoseley/manta/blob/main/examples/nexys_a7/video_sprite) example. This uses the core to store a 128x128 image sprite in 12-bit color, and outputs it to a VGA display at 1024x768. The sprite contents can be filled with an arbitrary image using the [send_image.py](https://github.com/fischermoseley/manta/blob/main/examples/nexys_a7/video_sprite/send_image.py) python script.

## Under the Hood

Each Block Memory core is actually a set of 16-bit wide BRAMs with their ports concatenated together, with any spare bits masked off. Here's a diagram:




This has one major consequence: if the core doesn't have a width that's an exact multiple of 16, Vivado will throw some warnings during synthesis as it optimizes out the unused bits. This is expected behavior (and rather convenient, actually).

The warnings are a little annoying, but not having to manually deal with the unused bits simplifies the implementation immensely - no Python is needed to generate the core, and it'll configure itself just based on Verilog parameters. This turns the block memory core from complicated beast requring a bunch of conditional instantiation in Python to a simple ~_100 line_ [Verilog file](https://github.com/fischermoseley/manta/blob/main/src/manta/block_memory.v).

### Address Assignment

Since each $n$-bit wide block memory is actually $ceil(n/16)$ BRAMs under the hood, addressing the BRAMs correctly from the bus is important. BRAMs are organized such that the 16-bit words that make up each entry in the Block Memory core are next to each other in bus address space. For instance, if one was to configure a core of width 34, then the memory map would be:

```
bus address :     | bram address
BUS_BASE_ADDR + 0 : address 0, bits [0:15]
BUS_BASE_ADDR + 1 : address 0, bits [16:31]
BUS_BASE_ADDR + 2 : address 0, bits [32:33]
BUS_BASE_ADDR + 3 : address 1, bits [0:15]
BUS_BASE_ADDR + 4 : address 1, bits [16:31]
...
```

corresponding to each


### Synchronicity

Since Manta's [data bus](../system_architecture) is only 16-bits wide, it's only possible to manipulate the BRAM core in 16-bit increments. This means that if you have a BRAM that's ≤16 bits wide, you'll only need to issue a single bus transaction to read/write one entry in the BRAM. However, if you have a BRAM that's ≥16 bits wide, you'll need to issue a bus transaction to update each 16-bit slice of it. For instance, updating a single entry in a 33-bit wide BRAM would require sending 3 messages to the FPGA: one for bits 1-16, another for bits 17-32, and one for bit 33. If your application expects each BRAM entry to update instantaneously, this could be problematic. Here's some exapmles:

!!! warning "Choice of interface matters here!"

    The interface you use (and to a lesser extent, your operating system) will determine the space between bus transactions. For instance, 100Mbit Ethernet is a thousand times faster than 115200bps UART, so issuing three bus transactions will take a thousanth of the time.

### Example 1 - ARP Caching
For instance, if you're making a network interface and you'd like to peek at your ARP cache that lives in a BRAM, it'll take three bus transactions to read each 48-bit MAC address. This will take time, during which your BRAM cache could update, leaving you with 16-bit slices that correspond to different states of the cache.

In a situation like this, you might want to pause writes to your BRAM while you dump its contents over serial. Implementing a flag to signal when a read operation is underway is simple - adding an [IO core](../io_core) to your Manta instance would accomplish this. You'd assert the flag in Python which disables writes to the user port on the FPGA, perform your reads, and then deassert the flag.

### Example 2 - Neural Network Accelerator
This problem would also arise if you were making a NN accelerator, with 32-bit weights stored in a BRAM updated by the host machine. Each entry would need two write operations, and during the time between the first and second write, the entry would contain a MSB from one weight, and a LSB from another. This may not be desirable - depending on what you do with your inference results, running the network with the invalid weight might be problematic.

If you can pause inference, then the flag-based solution with an IO core described in the prior example could work. However if you cannot pause inference, you could use a second BRAM as a cache. Run inference off one BRAM, and write new weights into another. Once all the weights have been written, assert a flag with an IO Core, and switch the BRAM that weights are obtained from. This guaruntees that the BRAM contents are always valid.