# Logic Analyzer

This emulates the look and feel of a logic analyzer, both benchtop and integrated. These work by continuously sampling a set of digital signals, and then when some condition (the _trigger_) is met, recording these signals to memory, which are then read out to the user.

Manta works exactly the same way, and the behavior of the logic analyzer is defined entirely in the Manta configuration file. Here's an example:

## Configuration

```yaml
---
cores:
  my_logic_analyzer:
    type: logic_analyzer
    sample_depth: 4096

    probes:
      larry: 1
      curly: 1
      moe: 1
      shemp: 4

    triggers:
      - moe RISING
      - curly FALLING
```

There's a few parameters that get configured here, including:

### Sample Depth

Which is just how many samples are saved in the capture. Having a larger sample depth will use more resources on the FPGA, but show what your probes are doing over a longer time.

### Probes

Probes are the signals you're trying to observe with the Logic Analyzer core. Whatever probes you specify in the configuration will be exposed by the `manta` module, which you then connect to your design in Verilog. Each probe has a name and a width, which is the number of bits wide it is.

### Triggers

Triggers are things that will cause the logic analyzer core to capture data from the probes. These get specified as a Verilog expression, and are partially reconfigurable on-the-fly. This will get elaborated on more as it's implemented, but if your trigger condition can be represented as a sum-of-products with each product being representable as an operator from the list [`==`, `!=`,`>`, `<`,`>=`, `<=`, `||`,`&&`, `^`]  along with a configurable register and a probe, you won't need to rebuild the bitstream to update the trigger condition. Whew, that was a mouthful.

### Trigger Position

The logic analyzer has a programmable _trigger position_, which sets when probe data is captured relative to the trigger condition being met. This is best explained with a picture:

For instance, setting the trigger position to `100` will cause the logic analyzer to save 100 samples of the probes prior to the trigger condition occuring. Manta uses a default holdoff value of `SAMPLE_DEPTH/2`, which positions the data capture window such that the trigger condition is in the middle of it.

### Operating Modes

The logic analyzer can operate in a number of modes, which govern what trigger conditions start the capture of data:

* __Single-Shot__: Once the trigger condition is met, record every subsequent sample until `SAMPLE_DEPTH` samples have been acquired. This is the mode most benchtop logic analyzers run in, so the Logic Analyzer Core defaults to this mode unless configured otherwise.
* __Incremental__: Record samples when the trigger condition is met, and don't record the samples when the trigger condition is not met. This is super useful for applications like audio processing or memory controllers, where there are many system clock cycles between signals of interest.
* __Immediate__: Read the probe states into memory immediately, regardless of if the trigger condition is met.

## Usage

### Capturing Data

Once you have your Logic Analyzer core on the FPGA, you can capture data with:

```
manta capture [config file] [LA core] [path] [path]
```

If the file `manta.yaml` contained the configuration above, and you wanted to export a .vcd and .mem of the captured data, you would execute:

```
manta capture manta.yaml my_logic_analyzer capture.vcd capture.mem
```

This will reset your logic analyzer, configure it with the triggers specified in `manta.yaml`, and perform a capture. The resulting .vcd file can be opened in a waveform viewer like [GTKWave](https://gtkwave.sourceforge.net/), and the `.mem` file can be used for playback as described in the following section.

Manta will stuff the capture data into as many files as you provide it on the command line, so if you don't want the `.mem` or `.vcd` file, just omit their paths.


### Playback

The LogicAnalyzerCore has the ability to capture a recording of a set of signals on the FPGA, and then 'play them back' inside a Verilog simulation. This requires generating a small Verilog module that loads a capture from a `.mem` file, which can be done by:

```
manta playback [config file] [LA core] [path]
```

If the file `manta.yaml` contained the configuration above, then running:

```
manta playback manta.yaml my_logic_analyzer sim/playback.v
```

Generates a Verilog wrapper at `sim/playback.v`, which can then be instantiated in the testbench in which it is needed. An example instantiation is provided at the top of the output verilog, so a simple copy-paste into the testbench is all that's necessary to use the module. This module is also fully synthesizable, so you can use it in designs that live on the FPGA too, if so you so wish.

## Examples