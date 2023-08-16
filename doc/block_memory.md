
## Overview
Block Memory (also called Block RAM, or BRAM) is the de facto means of storing data on FPGAs when the space needed exceeds a few registers. As a result, Manta provides a Block Memory core, which instantiates a dual-port BRAM on the FPGA. One port is provided to the host, and the other is connected to your logic with the standard BRAM interface (`addr`, `din`, `dout`, `wea`). This allows the host to provide reasonably large amounts of data to user logic - or the other way around, or a mix of both!

This is a very, very simple task - and while configuration is straightforward, there are a few caveats. More on both topics below:

## Configuration

Just like the rest of the cores, the Block Memory core is configured via an entry in a project's configuration file. This is easiest to show by example:

```yaml
---
cores:
  my_block_memory:
    type: block_memory
    width: 12
    depth: 16384

```

There's a few parameters that get configured here, including:

- `name`: The name of the Block Memory core. This name is used to reference the core when working with the API, and can be whatever you'd like.
- `type`: This denotes that this is a Block Memory core. All cores contain a `type` field, which must be set to `block_memory` to be recognized as an Block Memory core.

### Dimensions
The dimensions of the block memory are specified in the config file with the `width` and `depth` entries.

Manta won't impose any limit on the width or depth of the block memory you instantiate, but since Manta instantiates BRAM primitives on the FPGA, you will be limited by what your FPGA can support. It helps to know your particular FPGA's architecture here.

If your BRAM is more than 16 bits wide, check out the section on [Synchronicity](#synchronicity) and make sure your project will tolerate how Manta writes to the block memory.


### Python API

The Block Memory core functionality is stored in the `Manta.IOCore` and `Manta.IOCoreProbe` classes in [src/manta/io_core/\_\_init\_\_.py](https://github.com/fischermoseley/manta/blob/main/src/manta/io_core/__init__.py), and it may be controlled with the two functions:

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

\section{Block Memory Core}
\subsection{Description}
Block memory, also referred to as block RAM (BRAM), is a staple of FPGA designs. It consists of dedicated blocks of memory spaced throughout the FPGA die, and is very commonly used in hardware designs due to its configurability, simplicity, and bandwidth. Although each block memory primitive is made of fixed-function silicon, EDA tools allow them to be mapped to logical memories of arbitrary width and depth, combining and masking off primitives when necessary. These are exposed to the user’s logic over \textit{ports}, which contain four signals for reading and writing to the BRAM. These signals specify the address, input data, output data, and the desired operation (read/write) to the core. Most BRAM primitives include two ports, each of which may live on a separate clock domain, making them useful for clock domain crossing in addition to data storage. Each port can handle a memory operation on every clock edge, which is practically the maximum memory bandwidth possible in any digital system.

Central to Manta’s design objectives is the ability to debug user logic in an intuitive and familiar manner. Practically, this means being able to interact with bits on the FPGA in whatever method they’re presented. Block memory is one such method, and their pervasive use is acknowledged by the inclusion of a Block Memory Core in Manta. This core takes a standard dual-port, dual-clock BRAM and connects one port to Manta’s internal bus, and gives the other port to the user. This means that both the host machine and the user’s logic have access to the BRAM, allowing large amounts of data to be shared between both devices.

This is accomplished by architecting the Block Memory Core as shown in Figure \ref{fig_block_mem_core_arch}. Internally, the Block Memory Core consists of multiple BRAMs connected in parallel. This is done to maintain the ability to create block memory of arbitrary width and depth.  Manta’s internal bus uses 16-bit data words, so if a user wishes to create a BRAM of width $N$ where $N$ is larger than 16 bits, then multiple addresses in Manta’s memory are required to contain the data at a single BRAM address. These multiple addresses are created by creating many smaller block memories, each of which stores a 16-bit slice of the $N$-bit wide data. As a result, $ceil(\frac{N}{16})$ smaller BRAMs are needed to present a BRAM of width $N$ to the user. One set of ports on these smaller BRAMs are concatenated together, which presents a $N$ bit wide BRAM to the user. The other set of ports are individually connected to Manta’s internal bus.

\begin{figure}[h!]
\centering
\includegraphics[width=\textwidth]{block_memory_architecture.png}
\caption[Block diagram of the Block Memory Core.]{Block diagram of the Block Memory Core. Blocks in blue are clocked on the bus clock, and blocks in orange are clocked on the user clock.}
\label{fig_block_mem_core_arch}
\end{figure}