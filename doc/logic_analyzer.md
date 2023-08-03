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
    trigger_loc: 1000

    probes:
      larry: 1
      curly: 3
      moe: 9

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

Attached to each probe is a little piece of logic that allows you to check if some condition on the probe is true, and triggers the capture if so. These conditions look something like:
- `curly GEQ 2`
- `larry EQ 1`
- `moe NEQ 32`
- `larry RISING`
- `moe CHANGING`
- and so on!

Each of these contains a trigger, an operation, and an argument.

Triggers are things that will cause the logic analyzer core to capture data from the probes. Any one of them being satisfied is enough to start the capture. Each trigger can

### Trigger Position

The logic analyzer has a programmable _trigger position_, which sets when probe data is captured relative to the trigger condition being met. This is best explained with a picture:

_TODO: put a picture here @fischerm_

For instance, setting the trigger position to `100` will cause the logic analyzer to save 100 samples of the probes prior to the trigger condition occuring. Manta uses a default trigger position of `SAMPLE_DEPTH/2`, which positions the data capture window such that the trigger condition is in the middle of it.

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


## from thesis

\section{Logic Analyzer Core}
\subsection{Description}
\label{logic_analyzer_core_description}
Central to Manta's design is the ability to debug logic in a manner intuitive and familiar to 6.205 students. As such, Manta includes a logic analyzer tool that allows them to inspect their logic through a waveform display, similar to how it might be inspected through simulation. A typical workflow for using the core consists of the following:

\begin{itemize}
    \item The user describes the signals they would like to probe in the configuration file. The user provides a list of probe names and widths, which are needed to generate suitable Verilog.
    \item The user describes the \textit{trigger conditions} that must be met inside the FPGA fabric for a capture to begin. Triggers are defined as simple logical operations on probes, for instance checking if a probe named \texttt{foo} is equal to the number $3$, or if a probe named \texttt{bar} has just transitioned from high to low. The user also specifies the number of samples to be captured, referred to as the \textit{sample depth} of the core.
    \item Once fully configured, a Manta module is generated and flashed to the target FPGA with the process described in \ref{usage}.
    \item Once flashed, the user initiates the ILA from the host machine. This causes the Logic Analyzer Core to start sampling its inputs, waiting for the trigger condition to be met.
    \item Once met, the core begins saving the values of the probes to an internal block RAM called the \textit{sample memory}. This occurs every clock cycle until a number of samples equal to the sample depth has been captured, and the sample memory is full.
    \item Once complete, the host machine reads out the sample memory and stores it internally. This is then exported as a VCD file for use in a waveform viewer like GTKWave.
\end{itemize}

\begin{figure}[h!]
\centering
\includegraphics[width=\textwidth]{gtkwave.png}
\caption{A logic analyzer capture displayed in GTKWave.}
\label{gtkwave}
\end{figure}

This workflow is very similar to the behavior of the Xilinx ILA or a benchtop logic analyzer. This is intentional. FPGA engineers are familiar with on-chip logic analyzers, and electrical engineers are familiar with external logic analyzers. Very little is intended to be different, although a few extra features deserve mention:

\subsection{Features}
\subsubsection{Trigger Modes}
The behavior described in \ref{logic_analyzer_core_description} is referred to as single-shot trigger mode. This means that once the trigger condition is met, data is captured on every clock cycle in a continuous single shot. This is useful and the preferred behavior for most cases, but Manta also supports \textit{Incremental} and \textit{Immediate} trigger modes.

In Incremental mode, samples are only recorded to sample memory \textit{when} the trigger condition is met, not \textit{once} it is met. This allows slower-moving behavior to be captured. For instance, digital audio signals on a FPGA commonly use a 44.1kHz sampling frequency, but are routed through FPGA fabric clocked at hundreds of megahertz. As a result, many thousands of clock cycles may go by before a new audio sample is processed by the FPGA - filling the sample memory of a traditional logic analyzer with redundant data in the meantime. Placing Manta's Logic Analyzer into incremental mode solves this, as audio samples will only be saved to the sample memory when they change, assuming the trigger is configured correctly. In this case, the amount of memory required on the FPGA to capture a fixed number of audio samples is reduced by a thousandfold.

In Immediate mode, the trigger condition is ignored. The core begins filling the sample memory as soon as it is enabled, stopping only once the sample memory is filled. This allows the user to inspect the current state of their probes without a trigger condition. This is especially useful for investigating cases where a trigger condition is never being met, such as latchup or deadlock conditions. This mode is also useful for obtaining a random snapshot of the FGPA's state. The core is enabled by an interface (UART, Ethernet) that is slow relative to the clock speed of the FPGA fabric, meaning that the capture occurs at an effectively random time. Successive captures of this nature can be used to determine the ``average" state of onboard logic - what information is ``usually" on a bus, or what state a module is ``typically" in.

\subsubsection{Configurable Trigger Location}

In the scenario described in \ref{logic_analyzer_core_description}, the sample memory is written to as soon as the trigger condition is met - and not before. This only records the probe values after the trigger, but knowing the state of the FPGA immediately before is also rather useful. To do this, the core can be configured to buffer the last few clock cycles before the trigger condition. During this time the sample memory is used as a FIFO, and once the trigger condition occurs, samples are acquired until the sample memory is filled. The number of cycles to record ahead of the trigger is called the \textit{trigger position}. By default, most logic analyzers place the trigger condition in the middle of the acquisition such that there is equal amounts of data from before and after the trigger condition. To feel as intuitive and familiar as possible, Manta defaults to the same. However, this can be changed by writing to a register in the logic analyzer core.

\begin{figure}[h!]
\centering
\includegraphics[width=\textwidth]{trigger_positions.png}
\caption{Regions captured by the Logic Analyzer Core as trigger position is varied.}
\label{trigger_location_fig}
\end{figure}

\subsubsection{Simulator Playback}
Manta also allows data captured from the Logic Analyzer core to be ``played back'' in simulation. Any obtained capture data can be exported as a \texttt{.mem} file, which can be used in most simulators via the \texttt{readmemh} and \texttt{readmemb} Verilog functions. Manta autogenerates a convenient Verilog wrapper for this, allowing users to simulate logic with signals directly measured from the real world. This is useful for verifying that a testbench is providing the proper inputs to logic under test. This is useful for a few scenarios:

\begin{itemize}
    \item \textit{Input Verification.} This targets the common student experience in 6.205 of designs working in simulation, but failing in hardware. In the absence of any build errors, this usually means that the inputs being applied to the logic in simulation don't accurately represent those being applied to the logic in the real world. \footnote{Sometimes the toolchain will step in and modify the logic specified by the user. For example, if a net is driven by two nets at the same time, Vivado will connect the net to ground, and raise a critical warning. In this case, a valid bitstream is still generated, but it doesn't configure the FGPA in a way that will match simulation.} Playing signals back in simulation allows for easy comparison between simulated and measured input, and the state of the logic downstream.

    \item \textit{Sparse Sampling.} When users are debugging, their fundamental concern is the state of their logic. Normally this is obtained by sampling every net of interest with a logic analyzer probe, but for designs with a large amount of internal state sampling many signals requires significant block memory and lots of time to set up. If the design has fewer inputs than state variables, it requires fewer resources to sample the states and simulate the logic than to directly sample the state. For instance, debugging a misbehaving branch predictor in a CPU can be done by recording its address and data busses, playing them back in simulation, and inspecting the branch predictor there. This frees the user from having to sample the entire pattern history table, which would consume significant block memory.
\end{itemize}

\subsubsection{Reprogrammable Triggers}
Manta's triggers are reprogrammable, such that rebuilding source code is not necessary to change the trigger condition. Each of the logic analyzer's input probes has a trigger assigned to it, which continuously evaluates some combinational function on the input. This logic can be programmed to check for rising edges, falling edges or any change at all. It can also be programmed to check the result of a logical operation (such as $>$, $\leq$, $=$, $\neq$, etc.) against an \textit{argument}. The operation and argument for each probe's trigger are set with a pair of registers in Manta's memory.

The output of each of the individual triggers is then combined to trigger the logic analyzer core as a whole. These are combined with a $N$-input logic gate (either AND or OR) specified by the user through another register in memory. As a result the entire trigger configuration is specified by the state of Manta's memory, and changes to the configuration require resetting registers, not resynthesizing bitstreams.

However, this greatly restricts the trigger conditions users can specify. To mitigate this, Manta provides an option for an external trigger that allows for more complex triggers. When enabled, Manta adds an input port to the \texttt{manta} Verilog module, and triggers off its value, rather than the internal comparators. This allows users to provide their own Verilog to produce the desired trigger condition.

\subsection{Architecture}
The Logic Analyzer Core's implementation on the FPGA consists of three primary components:

\begin{itemize}
    \item The \textit{Finite State Machine (FSM)}, which controls the operation of the core. The FSM's operation is driven by its associated registers, which are placed in a separate module. This permits simple CDC between the bus and user clock domains.

    \item The \textit{Trigger Block}, which generates the core's trigger condition. The trigger block contains a trigger for each input probe, and the registers necessary to configure them. It also contains the $N$-logic gate (either AND or OR) that generates the core's trigger from the individual probe triggers. CDC is performed in exactly the same manner as the FSM. If an external trigger is specified, the trigger block is omitted from the Logic Analyzer Core, and the external trigger is routed to the FSM's \texttt{trig} input.

    \item The \textit{Sample Memory}, which stores the states of the probes during a capture. This is implemented as a dual-port, dual-clock block memory, with the bus on one port and the probes on the other. The probe-connected port only writes to the memory, with the address and enable pins managed by the FSM. CDC is performed in the block RAM primitive itself.
\end{itemize}

\begin{figure}[h!]
\centering
\includegraphics[width=\textwidth]{manta_logic_analyzer_architecture.png}
\caption[Block diagram of the Logic Analyzer Core.]{Block diagram of the Logic Analyzer Core. Blocks in blue are clocked on the bus clock, and blocks in orange are clocked on the user clock.}
\label{manta_logic_analyzer_architecture_fig}
\end{figure}
