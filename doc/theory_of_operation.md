# Theory of Operation

- Manta works by having a set of configurable debug cores daisy-chained together across a simple bus. Each core exposes some region of addressible memory that can be controlled by sending read and write commands to the FPGA over UART.

- These registers are 32-bits wide, and have a configurable address width. Manta will default to using the smallest possible address bus to minimize the burden on the place and route engine, but this can be overridden. This might be desirable if you wish to put other devices on the bus, such as a softcore.

- The regions of memory assigned to each core are determined by Manta when it autogenerates the Verilog HDL. Address space is assigned sequentially.

- Some registers, like captured sample data in a logic analyzer core, are not writeable by the host machine.

- Reading from a register will return the contents of the register over serial. Writing to a register will return nothing over serial. If you want to verify that the data you wrote to some location is valid, read from it after the write. This lack of a return makes things simpler for the state machines and faster for the user, since the OS on the host machine doesn't have to empty it's UART RX buffer before moving on in the Python.

These registers exist within whatever core you've asked manta to generate - be that an logic analyzer, or I/O. Each core is daisy-chained after the previous one in the arrangement shown below. This is done to provide maximum flexibility for place-and-route, as the critical timing path only exists between adjacent cores. If a hub-and-spoke arrangement were used, the critical timing path would exist between the hub and every spoke. For designs that span multiple clock domains and need to use BRAMs on the edges of clock domains for CDC, this makes designs that are very difficult to route. 

# Block Diagram



# Message-Passing Format

Data moves between the host computer and the FPGA over UART. UART's just an interface though, so the choice of what data to send is arbitrary. Manta encodes data exchanged between devices as messages, which are ASCII text in the following format:

```[preamble] [address] [data (optional)] [EOL]``` 

- The __preamble__ is just the character `M`, encoded as ASCII.

- The __address__ is the memory location we wish to access. This must exist somewhere in the address space consumed by the cores. If it does not, then a write operation addressed here will do nothing, and a read operation addressed here will return nothing. The address itself is transmitted as hex values, encoded as ASCII using the characters `0-9` and `A-F`. All addresses are a single byte, so ther can not be more than 256 register locations onboard.

- The __data__ gets stored in the memory location provided by __address__. The presence of any number of data bytes indicates a write operation, while no data bytes indicates a read operation.

- An __EOL__ indicates the end of the message. CR, LF, or both are considered valid delimiters to for messages sent to the FPGA. For messages sent to the host machine, the FPGA will send CRLF.

## Example Messages

Some examples of valid messages to the FPGA are:
```MBEEF\r\n```, which writes `0xEF` to the memory at location `0xBE`.
```MBE\r\n```, which reads the value of the memory at location `0xBE`.

Some examples of invalid messages to the FPGA are:
```MBEEEF\r\n```f, which contains 12 bits of data, which isn't a multiple of 8.
```NBEEF\r\n```, which contains the wrong preamble.


# AXI-ish Interfaces