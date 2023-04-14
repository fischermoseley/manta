
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

## Cores

### Logic Analyzer Core

### Block Diagram

<div class="mxgraph" style="max-width:100%;border:1px solid transparent;" data-mxgraph="{&quot;highlight&quot;:&quot;#0000ff&quot;,&quot;nav&quot;:true,&quot;resize&quot;:true,&quot;page&quot;:1,&quot;toolbar&quot;:&quot;pages zoom layers tags lightbox&quot;,&quot;edit&quot;:&quot;_blank&quot;,&quot;xml&quot;:&quot;&lt;mxfile host=\&quot;app.diagrams.net\&quot; modified=\&quot;2023-03-22T17:11:45.384Z\&quot; agent=\&quot;5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36\&quot; etag=\&quot;sX6QVJwPZ_vy7T_roZSM\&quot; version=\&quot;20.8.20\&quot; type=\&quot;google\&quot; pages=\&quot;2\&quot;&gt;&lt;diagram id=\&quot;DuXDLgHd7OUu3MXjHNdG\&quot; name=\&quot;top_level\&quot;&gt;7ZbLjtowFIafJsuiXIYEloRhYFGkqlTq2o1PEgvHTh2HAE9fe2IDwWUKi2lnURbB5/P9/8+J4kXzar8UqC7XHAP1Qh/vvejZC8MoeVJPDQ49SJ6CHhSC4B5dgA05goG+oS3B0AwGSs6pJPUQZpwxyOSAISF4NxyWczrctUYFOGCTIerS7wTLsqeTsX/mKyBFaXcOfNNTITvYgKZEmHcXKFp40VxwLvtWtZ8D1dpZXfp5Lzd6TwcTwOQ9E9i31WoNy+l6wbbp8XmZj4+7T3G/yg7R1lw4/TpbmwPLg1Wh6UhFEVNRmpWE4s/owFu9ayNRtrVRKqBRBn6xRwqu0BrprPAVVdOENGaHGpSyomaGey9z1R0ICfsLZO65BF6BFAc1xPROp/7Iv/iN+wUONrUiY0l3djSwNpVDN00mmSwqTludhVYNo/UDuieO7jUXUpHZW9o/Jtubhv9ZS6NW6GoV/0aq6XspFbpSeWFMdbrlnGnJGvvSiH+2upjS4NxUrUL/Y8LsrB/iBHXWOhRhLFzaAXLhbaKu2p/O4itTlfhy6F8jBd/CnFMuFGH81fCcUHqFECUFUyGFXK+gjSTqdTUzuCIY603SriQSNjXK9I6dejfrYuQtw4BNEeoDmmQKAhO/oIpQ7fwK6A70yqbDngJDjloq70+45OGEm4yS8V05FwejcPxOaTe5VaCul/+qQPdDZT5KvbrK/a9XFYpe+49fsJO7E/AvFawKz19Jr30Xn5rR4hc=&lt;/diagram&gt;&lt;diagram name=\&quot;logic_analyzer\&quot; id=\&quot;VT9R2HSR_r-PYTjt5Vqh\&quot;&gt;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&lt;/diagram&gt;&lt;/mxfile&gt;&quot;}"></div>
<script type="text/javascript" src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>

Nominal interaction with the logic analyzer core should be:
- Check state - if it's in anything other than idle, request to stop the existing capture
- Once state's in IDLE, go ahead and configure trigger positions and conditions and request start. Also set it back down to zero.
- Wait for state to be in captured. If you want a timeout, then pulse stop_request once the timeout has expired.
- Read out contents from memory
- Pulse stop_request to end the capture and return the state back to IDLE

