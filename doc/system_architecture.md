
# How it Works
Manta works by having a set of configurable cores daisy-chained together across a simple bus that resembles AXI-lite. Each core exposes some region of addressible memory, which is accessed by the host machine over an interface of choice. Here's what this looks like as a block diagram, in this case UART is used as the interface:

## Bus

This daisy-chaining is done to make place-and-route as easy as possible - the critical timing path only exists between adjacent cores, instead of rouing back to some central core in a hub-and-spoke arrangement. This relaxed routing helps designs that span multiple clock domains and require BRAMs placed on the edges of clock domains for CDC.  

## Memory

The memory is built of 16-bit registers living on a 16-bit address bus. Address space is assigned when the Verilog is generated, since each core can occupy a varying amount of address space depending on how it's configured. This space is assigned sequentially - the first core in the chain will occupy the first section of memory, and the last core will occupy the last section. Some registers are read-only to the host machine, and attempts to write to them will be ignored by the core.

## Read/Write Transactions

As you'd expect, reading from some address will elicit a response from the FGPA. However, writing to some address __will not__. If you want to verify that the data you wrote to some location is valid, read from it after the write. This is done to keep state machines simple and interfaces fast. 

Data moves between the host computer and the FPGA over UART. UART's just an interface though, so the choice of what data to send is arbitrary. Manta encodes data exchanged between devices as messages, which are ASCII text in the following format:

```[preamble] [address] [data (optional)] [EOL]``` 

- The __preamble__ is just the character `M`, encoded as ASCII.

- The __address__ is the memory location we wish to access. This must exist somewhere in the address space consumed by the cores. If it does not, then read/write operations addressed here will do nothing. The address itself is transmitted as hex values, encoded as ASCII using the characters `0-9` and `A-F`.

- The __data__ gets stored in the memory location provided by __address__. The presence of any number of data bytes indicates a write operation, while no data bytes indicates a read operation.

- An __EOL__ indicates the end of the message. CR, LF, or both are considered valid delimiters to for messages sent to the FPGA. For messages sent to the host machine, the FPGA will send CRLF.

This message format can be either a sequence of bytes encoded over UART, or characters in a data field of an Ethernet packet.

### Example Messages

Some examples of valid messages to the FPGA are:
```MBEEF\r\n```, which writes `0xEF` to the memory at location `0xBE`.
```MBE\r\n```, which reads the value of the memory at location `0xBE`.

Some examples of invalid messages to the FPGA are:
```MBEEEF\r\n```f, which contains 12 bits of data, which isn't a multiple of 8.
```NBEEF\r\n```, which contains the wrong preamble.

For example, `M1234\r\n` specifies a read operation at address `0x1234` in the memory, and if that location contains the data `0x5678`, it will produce a response of `M5678\r\n`.

## Python API

The Python API has two main purposes: to generate the Verilog required to instantiate debug cores on the FPGA, and to let the user easily interact with said cores. The exact Verilog and memory operations are dependent on the cores being configured and the interface between the host machine and the FPGA. This information is stored in a YAML (or JSON) configuration file, which is used to configure an instance of the `Manta` class. This maintains instances of `IOCore`, `LogicAnalyzerCore`, `LUTRAMCore`, and `BRAMCore` according to the given configuration.

### Loading configuration

Let's use the following configuration as an example: 

```yaml

---
cores:
  my_io_core:
    type: io

    inputs:
      btnc: 1
      sw: 16

    outputs:
      led: 16
      led16_b: 1
      led16_g: 1
      led16_r: 1

  my_logic_analyzer:
    type: logic_analyzer
    sample_depth: 4096
    
    probes:
      larry: 1
      curly: 1
      moe: 1
      shemp: 4
      
    triggers:
    - larry && curly && ~moe

  my_lut_ram:
    type: lut_ram 
    size: 64 

uart:
  port: "/dev/tty.usbserial-2102926963071"
  baudrate: 115200
  clock_freq: 100000000
```

For each core in the config file, an instance of the corresponding Python object is added to the `Manta` object. For instance, the `Manta` instance created by the configuration above will include an `IOCore`, a `LogicAnalyzerCore`, and a `LUTRAMCore`. Each Core object is instantiated by providing the appropriate section of the config file - for instance, the logic analyzer in the config above will be created by calling `LogicAnalyzerCore(foo)`, where `foo` is:

```yaml
my_logic_analyzer:
    type: logic_analyzer
    sample_depth: 4096
    
    probes:
      larry: 1
      curly: 1
      moe: 1
      shemp: 4
      
    triggers:
    - larry && curly && ~moe
```
Stored as pythonic key-value representation. Each core also checks to make sure it's been given a sensible configuration when it is instantiated - this means the class constructors are mostly assertions about the configuration.

### Generating HDL

Once all the cores have been instantiated and stored in the `Manta` instance, Verilog can be generated. Just like how verifying each core's configuration is left up to core's corresponding Python object, generating the HDL is also left up to each core's corresponding Python object. All that's required is for each core to implement three methods:

- `hdl_inst`, which returns the module instantiation in Verilog as a python string. Any ports that need to connect to modules upstream or downstream on the bus aren't configured by the core. Those connections are made in `Manta.generate_hdl()`, which calls `Manta.generate_insts()`.
- `hdl_def`, which returns the module definition in Verilog as a Python string. This is usually either generated on-the-fly, or loaded from the Verilog source files included in the Python wheel via `pkgutil`.
- `hdl_top_level_ports`, which returns a list of any ports that the core needs tied to the top-level declaration of the `manta` module. Usually these are probes going to Logic Analyzers or IO Cores, or the TX/RX lines needed by a UART interface.

Once these have been obtained for each core, the `Manta.generate_hdl()` method will patch them all together to produce `manta.v`, which is a single file that contains all the Verilog needed to instantiate Manta. This file has the following anatomy:

- Asking each core to generate HDL instantiations, definitions, and top_level ports.
- These then get assembled into the following parts of the file:
    - __Header__ - contains a little blurb about when and who generated the file
    - __Top-Level Module__ - the actual definition of module manta
        - __Declaration__ - contains `module manta` and top-level ports
                        that constitutent cores need access to
        - __Interface RX__ - the modules needed to bring whatever interface the user
                            selected onto the bus. For UART, this is just an instance
                            of uart_rx and bridge_rx.
        - __Core Chain__ - the chain of cores specified by the user. This follows
                        a sequence of:
            - Core Instance - HDL specifying an instance of the core.
            - Core Connection - HDL specifying the registers that connect one
                                core to the next.
            - Core Instance
            - Core Connection
            ....

            This repeats for however many cores the user specified.

        - __Interface TX__ - the modules needed to bring the bus out to whatever
                            interface the user selected. For UART, this is just
                            an instance of bridge_tx and uart_tx.
        - __Footer__ - just the 'endmodule' keyword.

    - __Module Definitions__ - all the source for the modules instantiated in the
                            top-level module.


### Using Cores

Once manta's been generated, included in your project, and built, the Python API provides methods for interfacing with the cores.