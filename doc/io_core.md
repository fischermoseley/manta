
## Overview
Registers are a fundamental building block of digital hardware. Registers store values as they move throughout the FPGA, and are operated on by the logic placed onboard the chip. Interfacing with this logic in an intuitive manner is Manta’s primary design objective, and as a result it includes an Input/Output (IO) core to directly measure and control arbitrary signals on the FPGA. This is done by routing them to registers, which are then exposed to the host over Manta’s internal bus.

<img src="/assets/io_core_block_diagram.png" alt="drawing" width="400"/>

This is done with the architecture shown in Figure \ref{io_core_block_diagram}. A series of connections are made to the user’s logic. These are called \textit{probes}, and each may be either an input or an output. If the probe is an input, then its value is taken from the user’s logic, and stored in a register that may be read by the host machine. If the probe is an output, then its value is provided to the user’s logic from a register written to by the host. The widths of these probes is arbitrary, and is set by the user at compile-time.

However, the connection between these probes and the user’s logic is not direct. The state of each probe is buffered, and the buffers are updated when a \textit{strobe} register within the IO core is set by the host machine. During this update, new values for output probes are provided to user logic, and new values for input probes are read from user logic.

This is done to mitigate the possibility of an inconsistent system state. Although users may configure registers of arbitrary width, Manta’s internal bus uses 16-bit data words, meaning operations on probes larger than 16 bits require multiple bus transactions. These transactions occur over some number of clock cycles, with an arbitrary amount of time between each.

This can easily cause data corruption if the signals were unbuffered. For instance, a read operation on an input probe would read 16 bits at a time, but the probe’s value may change in the time that passes between transactions. This would cause the host to read a value for which each 16 bit chunk corresponds to a different moment in time. Taken together, these chunks may represent a value that the input probe never had. Similar corruption would occur when writing to an unbuffered output probe. The value of the output probe would take multiple intermediate values as each 16-bit section is written by the host. During this time the value of the output probe is not equal to either the incoming value from the host, or the value the host had previously written to it. The user logic connected to the output probe has no idea of this, and will dutifully use whatever value it is provided. This can very easily induce undesired behavior in the user’s logic, as it is being provided inputs that the user did not specify.

Buffering the probes mitigates these issues, but slightly modifies the way the host machine uses the core. When the host wishes to read from an input probe, it will set and then clear the strobe register, which pulls the current value of the probe into the buffer. The host then reads from buffer, which is guaranteed to not change as it is being read from. Writing to an output probe is done in much the same way. The host writes a new value to the buffer, which is flushed out to the user’s logic when the strobe register is set and cleared. This updates every bit in the output probe all at once, guaranteeing the user logic does not observe any intermediate values.

These buffers also provide a convenient location to perform clock domain crossing. Each buffer is essentially a two flip-flop synchronizer, which allows the IO core to interact with user logic on a different clock than Manta’s internal bus.





% \begin{figure}[h!]
% \centering
% \includegraphics[width=0.8\textwidth]{io_core_memory_map}
% \caption{Memory map of an IO core.}
% \label{io_core_memory_map}
% \end{figure}


!!! warning "This isn't magic!"

    While the IO Core has been designed to be as fast as possible,
    setting and querying registers is nowhere near instantaneous!
    If you're trying to set values in your design with cycle-accurate
    timing, this will not do that for you.

## Options
- `inputs`
- `outputs`

## Example Configuration

```yaml
---
the_muppets_io_core:
  type: io

  inputs:
    kermit: 3
    piggy: 68
    animal: 1
    scooter: 4

  outputs:
    fozzy: 1
    gonzo: 3

uart:
  baudrate: 115200
  port: "/dev/tty.usbserial-2102926963071"
```

## Python API

The caveat being that Manta is limited by the bandwidth of PySerial, which is limited by your operating system and system hardware. These calls may take significant time to complete, and __they are blocking__. More details can be found in the API reference.

### Example

```python
>>> import Manta
>>> m = Manta('manta.yaml')
>>> m.my_io_core.fozzy.set(True)
>>> m.my_io_core.gonzo.set(4)
>>> m.my_io_core.scooter.get()
5
```

## How It Works
