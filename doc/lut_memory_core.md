A LUT Memory Core is simply just a set of registers that live on the bus, and thus implemented in Look Up Tables (LUTs). Their only connection is to the bus, so they aren't reachable from user code. For bus-tied memory that's interfaceable with user code, consider the [Block Memory Core](../block_memory_core).

LUT Memory Cores are convenient for when the host machine needs to store a small amount of data on the FPGA, accessible only to itself.

I have no idea under what circumstances this would be useful, but perhaps someone with fresher eyes then mine would be able to see something. @Joe, thoughts?

## Configuration

Just like every core, a given LUT Memory core is described in Manta's configuration file:

```yaml
cores:
  my_lut_ram:
    type: lut_ram
    size: 64
```

Each register is 16-bits wide, so the only configuration option is just the size of the memory.

## Python
The core can be written to and read from in Python with the following:

```python
m.my_lut_ram.write(addr, data)
foo = m.my_lut_ram.read(addr)
```

## Examples
A LUT Memory core is used in the lut_ram examples, for both the [nexys_a7](https://github.com/fischermoseley/manta/tree/main/examples/nexys_a7/lut_ram) and the [icestick](https://github.com/fischermoseley/manta/tree/main/examples/icestick/lut_ram).