# IO Core


!!! warning "This isn't magic!"

    While the IO Core has been designed to be as fast as possible, 
    setting and querying registers is nowhere near instantaneous! 
    If you're trying to set values in your design with cycle-accurate
    timing, this will not do that for you.

## Configuration

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
    fozzy: 2
    gonzo: 3 

uart:
  baudrate: 115200
  port: "/dev/tty.usbserial-2102926963071"
```

## Python API
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


## How does it work?

Each probe set in the config file maps to a single address on the bus. However the address points to a data register that's only 16-bits wide, so for probe widths larger than that we map to multiple registers. 

This gets a little weird. Normally each register would update as soon as it receives a new value from the interface, but doing so here would cause parts of the probe to update at different times. This is usually not desireable, so instead a copy of the probe state is maintained inside the IO core. In the case of an output core, this copy gets modified whenever write operations are performed on that section of memory, but _only on a write operation to the last register_ does this buffer get clocked out to the rest of the FPGA. Similiarly for an input core, we maintain a local copy, but that gets clocked in __on a read operation from the first register__. This makes sure that the operation remains atomic with respect to the whole port, not just every 16 bits of it.

This does mean that a write operation to the last register/a read operation from the first register will cause data to be clocked out of/into the core. This allows for some flexibility in how packets are sent to the device.