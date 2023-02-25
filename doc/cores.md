# Cores

Manta has two types of debug cores: a logic analyzer core, and an IO core.

## Logic Analyzer Core

This emulates the look and feel of a logic analyzer, both benchtop and integrated. These work by continuously sampling a set of digital signals, and then when some condition (the _trigger_) is met, recording these signals to memory, which are then read out to the user. 

Manta works exactly the same way, and the behavior of the logic analyzer is defined entirely in the Manta configuration file. Here's an example:

```yaml
---
logic_analyzer:
  sample_depth: 4096
  clock_freq: 100000000

  probes:
    larry: 1
    curly: 1
    moe: 1
    shemp: 4
    
  triggers:
  - larry && curly && ~moe

uart:
  baudrate: 115200
  port: "/dev/tty.usbserial-2102926963071"
  data: 8
  parity: none
  stop: 1
  timeout: 1
```

There's a few parameters that get configured here, including:

### Probes

Probes are the signals read by the core. These are meant to be connected to your RTL design when you instantiate your generated copy of Manta. These can be given whatever name and width you like (within reason). You can have up to 256 probes in your design. 

### Sample Depth

Sample depth controls how many samples of the probes get read into the buffer.

### Triggers

Triggers are things that will cause the logic analyzer core to capture data from the probes. These get specified as a Verilog expression, and are partially reconfigurable on-the-fly. This will get elaborated on more as it's implemented, but if your trigger condition can be represented as a sum-of-products with each product being representable as an operator from the list [`==`, `!=`,`>`, `<`,`>=`, `<=`, `||`,`&&`, `^`]  along with a configurable register and a probe, you won't need to rebuild the bitstream to update the trigger condition. Whew, that was a mouthful.

### Operating Modes

The logic analyzer can operate in a number of modes, which govern what trigger conditions start the capture of data:

* __Single-Shot__: When the trigger condition is met, grab the whole thing.
* __Incremental__: Only pull values when the trigger condition is met. Ignore values received while the trigger condition is not met,
* __Immediate__: Read the probe states into memory immediately, regardless of if the trigger condition is met.

### Holdoff

The logic analyzer has a programmable _holdoff_, which sets when probe data is captured relative to the trigger condition being met. For instance, setting the holdoff to `100` will cause the logic analyzer to start recording probe data 100 clock cycles after the trigger condition occuring. 

Holdoff values can be negative! When this is configured, new probe values are being continuously pushed to the buffer, while old ones are pushed off. This measns that the probe data for the last `N` timesteps can be saved, so long as `N` is not larger than the depth of the memory.  

Manta uses a default holdoff value of `-SAMPLE_DEPTH/2`, which positions the data capture window such that the trigger condition lives in the middle of it. Here's a diagram:

Similarly, a holdoff of `-SAMPLE_DEPTH` would place the trigger condition at the right edge of the trigger window. A holdoff of `0` would place the trigger at the left edge of the window. Postive holdoff would look like this:


## IO Core

_More details to follow here as this gets written out, for now this is just a sketch_

This emulates the look and feel of an IO pin, much like what you'd find on a microcontroller. 

Manta provides a Python API to control these - which allows for behavior like:

```python
>>> import manta.api
>>> cores = manta.api.generate('manta.yaml')
>>> io = cores.my_io_core
>>> io.probe0.set(True)
>>> io.probe0.set(False)
>>> io.probe1.read()
True
```

The caveat being that Manta is limited by the bandwidth of PySerial, which is limited by your operating system and system hardware. These calls may take significant time to complete, and __they are blocking__. More details can be found in the API reference.

## Everything Else

Manta needs to know what clock frequency you plan on running it at so that it can progperly generate the baudrate you desire. It also needs to know what serial port your FPGA is on, as well as how to configure the interface. Right now only standard 8N1 serial is supported by the FPGA.