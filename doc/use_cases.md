Manta's capabilities are best reflected in its cores, for which a brief description of each is provided below:

### __Logic Analyzer Core__

_More details available on the [full documentation page](./logic_analyzer_core.md)._

This core captures a timeseries of digital signals from within the FPGA, much like a benchtop logic analyzer would. This captures data on the FPGA's native clock and presents it as a waveform, making it very useful for debugging logic cycle-by-cycle. This concept is very similar to the Xilinx [Integrated Logic Analyzer (ILA)](https://docs.xilinx.com/r/en-US/ug908-vivado-programming-debugging/ILA) and Intel [SignalTap](https://www.intel.com/content/www/us/en/docs/programmable/683819/21-3/logic-analyzer-introduction.html) utilities.

You may find this core useful for:

* _Verifying specification adherence for connected hardware_ - for instance, you're writing a S/PDIF decoder that works in simulation, but fails in hardware. The logic analyzer core can record a cycle-by-cycle capture of what's coming off the cable, letting you verify that your input signals are what you expect. Even better, Manta will let you play that capture back in your preferred simulator, letting you feed the exact same inputs to your module in simulation and check your logic.

* _Capturing arbitrary data_ - you're working on a DSP project, and you'd like to grab some test data from your onboard ADCs to start prototyping your signal processing with. Manta will grab that data, and export it for you.

### __I/O Core__

_More details available on the [full documentation page](./io_core.md)._

This core presents a series of user-accessbile registers to the FPGA fabric, which may be configured as either inputs or outputs. The value of an input register can be read off the FPGA by the host machine, and the value of an output register on the FPGA may be set by the host machine. This is handy for getting small amounts of information into and out of the FPGA, debugging, configuration, or experimentation. This concept is very similar to the Xilinx [Virtual IO](https://docs.xilinx.com/v/u/en-US/pg159-vio) and Intel [In-System Sources and Probes](https://www.intel.com/content/www/us/en/docs/programmable/683552/18-1/in-system-sources-and-probes-66964.html) tools.

You may find this core useful for:

* _Prototyping designs in Python, and incrementally migrating them to hardware_ - you're working on some real-time signal processing, but you want to prototype it with some sample data in Numpy before meticulously implementing everything in Verilog.

* _Making dashboards_ - you'd like to get some telemetry out of your existing FPGA design and display it nicely, but you don't want to implement an interface, design a packetization scheme, and write a library.

### __Memory Cores__

_More details available on the [full documentation page](./memory_core.md)._

This core creates a two-port block memory on the FPGA, and gives one port to the host machine, and the other to your logic on the FPGA. The width and depth of this block memory is configurable, allowing large chunks of arbitrarily-sized data to be shuffled onto and off of the FPGA by the host machine, via the Python API. This lets you establish a transport layer between the host and FPGA, that treats the data as exactly how it exists on the FPGA.

You may find this core useful for:

* _Moving data between a host and connected FPGA_ - you're working on a cool new machine learning accelerator, but you don't want to think about how to get training data and weights out of TensorFlow, and into your core.

* _Hand-tuning ROMs_ - you're designing a digital filter for a DSP project and would like to tune it in real-time, or you're developing a soft processor and want to upload program code without rebuilding a bitstream.
