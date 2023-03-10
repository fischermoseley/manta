
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
