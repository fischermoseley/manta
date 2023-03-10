# IO Core

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