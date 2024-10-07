from amaranth import *
from manta.utils import *
from manta.memory_core import MemoryCore
from manta.logic_analyzer.trigger_block import LogicAnalyzerTriggerBlock
from manta.logic_analyzer.fsm import LogicAnalyzerFSM, States, TriggerModes
from manta.logic_analyzer.playback import LogicAnalyzerPlayback


class LogicAnalyzerCore(MantaCore):
    """
    A module for generating a logic analyzer on the FPGA, with configurable
    triggers, trigger position, and trigger modes.

    Provides methods for generating synthesizable logic for the FPGA, as well
    as methods for reading and writing the value of a register.

    More information available in the online documentation at:
    https://fischermoseley.github.io/manta/logic_analyzer_core/
    """

    def __init__(self, config, base_addr, interface):
        self._config = config
        self._interface = interface
        self._check_config()

        # Bus Input/Output
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        self._probes = [
            Signal(width, name=name) for name, width in self._config["probes"].items()
        ]

        # Submodules
        self._fsm = LogicAnalyzerFSM(self._config, base_addr, self._interface)
        self._trig_blk = LogicAnalyzerTriggerBlock(
            self._probes, self._fsm.get_max_addr() + 1, self._interface
        )

        self._sample_mem = MemoryCore(
            mode="fpga_to_host",
            width=sum(self._config["probes"].values()),
            depth=self._config["sample_depth"],
            base_addr=self._trig_blk.get_max_addr() + 1,
            interface=self._interface,
        )

    @property
    def max_addr(self):
        return self._sample_mem.max_addr

    @property
    def top_level_ports(self):
        return self._probes

    def _check_config(self):
        # Check for unrecognized options
        valid_options = [
            "type",
            "sample_depth",
            "probes",
            "triggers",
            "trigger_location",
            "trigger_mode",
        ]
        for option in self._config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in Logic Analyzer.")

        # Check sample depth is provided and positive
        sample_depth = self._config.get("sample_depth")
        if not sample_depth:
            raise ValueError("Logic Analyzer must have sample_depth specified.")

        if not isinstance(sample_depth, int) or sample_depth <= 0:
            raise ValueError("Logic Analyzer sample_depth must be a positive integer.")

        # Check probes
        if "probes" not in self._config or len(self._config["probes"]) == 0:
            raise ValueError("Logic Analyzer must have at least one probe specified.")

        for name, width in self._config["probes"].items():
            if width < 0:
                raise ValueError(f"Width of probe {name} must be positive.")

        # Check trigger mode, if provided
        trigger_mode = self._config.get("trigger_mode")
        valid_modes = ["single_shot", "incremental", "immediate"]
        if trigger_mode and trigger_mode not in valid_modes:
            raise ValueError(
                f"Unrecognized trigger mode {self._config['trigger_mode']} provided."
            )

        # Check triggers
        if trigger_mode and trigger_mode != "immediate":
            if "triggers" not in self._config or self._config["triggers"] == 0:
                raise ValueError(
                    "Logic Analyzer must have at least one trigger specified if not running in immediate mode."
                )

        # Check trigger location
        trigger_location = self._config.get("trigger_location")
        if trigger_location:
            if not isinstance(trigger_location, int) or trigger_location < 0:
                raise ValueError("Trigger location must be a positive integer.")

            if trigger_location >= self._config["sample_depth"]:
                raise ValueError("Trigger location must be less than sample depth.")

            if trigger_mode == "immediate":
                warn(
                    "Ignoring option 'trigger_location', as 'trigger_mode' is set to immediate, and there is no trigger condition to wait for."
                )

        # Check triggers themselves
        if trigger_mode == "immediate":
            if "triggers" in self._config:
                warn(
                    "Ignoring triggers as 'trigger_mode' is set to immediate, and there are no triggers to specify."
                )

        else:
            if ("triggers" not in self._config) or (len(self._config["triggers"]) == 0):
                raise ValueError("At least one trigger must be specified.")

            for trigger in self._config.get("triggers"):
                if not isinstance(trigger, str):
                    raise ValueError("Trigger must be specified with a string.")

                # Trigger conditions may be composed of either two or three components,
                # depending on the operation specified. In the case of operations that
                # don't need an argument (like DISABLE, RISING, FALLING, CHANGING) or
                # three statements in

                # Check the trigger operations
                components = trigger.strip().split(" ")
                if len(components) == 2:
                    name, op = components
                    if op not in ["DISABLE", "RISING", "FALLING", "CHANGING"]:
                        raise ValueError(
                            f"Unable to interpret trigger condition '{trigger}'."
                        )

                elif len(components) == 3:
                    name, op, arg = components
                    if op not in ["GT", "LT", "GEQ", "LEQ", "EQ", "NEQ"]:
                        raise ValueError(
                            f"Unable to interpret trigger condition '{trigger}'."
                        )

                else:
                    raise ValueError(
                        f"Unable to interpret trigger condition '{trigger}'."
                    )

                # Check probe names
                if components[0] not in self._config["probes"]:
                    raise ValueError(f"Unknown probe name '{components[0]}' specified.")

    def elaborate(self, platform):
        m = Module()

        # Add submodules
        m.submodules.fsm = self._fsm
        m.submodules.sample_mem = self._sample_mem
        m.submodules.trig_blk = self._trig_blk

        # Concat all the probes together, and feed to input of sample memory
        # (it is necessary to reverse the order such that first probe occupies
        # the lowest location in memory)
        m.d.comb += self._sample_mem.user_data_in.eq(Cat(self._probes[::-1]))

        # Wire bus connections between internal modules
        m.d.comb += [
            # Bus Connections
            self._fsm.bus_i.eq(self.bus_i),
            self._trig_blk.bus_i.eq(self._fsm.bus_o),
            self._sample_mem.bus_i.eq(self._trig_blk.bus_o),
            self.bus_o.eq(self._sample_mem.bus_o),
            # Non-bus Connections
            self._fsm.trigger.eq(self._trig_blk.trig),
            self._sample_mem.user_addr.eq(self._fsm.write_pointer),
            self._sample_mem.user_write_enable.eq(self._fsm.write_enable),
        ]

        return m

    def capture(self, verbose=False):
        """
        Performs a capture, recording the state of all input probes to the
        FPGA's memory, and then returns that as a LogicAnalyzerCapture class
        on the host.
        """
        print_if_verbose = lambda x: print(x) if verbose else None

        # If core is not in IDLE state, request that it return to IDLE
        print_if_verbose(" -> Resetting core...")
        state = self._fsm.registers.get_probe("state")
        if state != States.IDLE:
            self._fsm.registers.set_probe("request_start", 0)
            self._fsm.registers.set_probe("request_stop", 0)
            self._fsm.registers.set_probe("request_stop", 1)
            self._fsm.registers.set_probe("request_stop", 0)

            if self._fsm.registers.get_probe("state") != States.IDLE:
                raise ValueError("Logic analyzer did not reset to IDLE state.")

        # Set triggers
        print_if_verbose(" -> Setting triggers...")
        self._trig_blk.clear_triggers()

        if self._config.get("trigger_mode") != "immediate":
            self._trig_blk.set_triggers(self._config)

        # Set trigger mode, default to single-shot if user didn't specify a mode
        print_if_verbose(" -> Setting trigger mode...")
        if "trigger_mode" in self._config:
            mode = self._config["trigger_mode"].upper()
            self._fsm.registers.set_probe("trigger_mode", TriggerModes[mode])

        else:
            self._fsm.registers.set_probe("trigger_mode", TriggerModes.SINGLE_SHOT)

        # Set trigger location
        print_if_verbose(" -> Setting trigger location...")
        if "trigger_location" in self._config:
            self._fsm.registers.set_probe(
                "trigger_location", self._config["trigger_location"]
            )

        else:
            self._fsm.registers.set_probe(
                "trigger_location", self._config["sample_depth"] // 2
            )

        # Send a start request to the state machine
        print_if_verbose(" -> Starting capture...")
        self._fsm.registers.set_probe("request_start", 0)
        self._fsm.registers.set_probe("request_start", 1)
        self._fsm.registers.set_probe("request_start", 0)

        # Poll the state machine's state, and wait for the capture to complete
        print_if_verbose(" -> Waiting for capture to complete...")
        while self._fsm.registers.get_probe("state") != States.CAPTURED:
            pass

        # Read out the entirety of the sample memory
        print_if_verbose(" -> Reading sample memory contents...")
        addrs = list(range(self._config["sample_depth"]))
        raw_capture = self._sample_mem.read(addrs)

        # Revolve the memory around the read_pointer, such that all the beginning
        # of the caputure is at the first element
        print_if_verbose(" -> Checking read pointer and revolving memory...")
        read_pointer = self._fsm.registers.get_probe("read_pointer")

        data = raw_capture[read_pointer:] + raw_capture[:read_pointer]
        return LogicAnalyzerCapture(data, self._config, self._interface)


class LogicAnalyzerCapture:
    """
    A container class for the data collected by a LogicAnalyzerCore. Contains
    methods for exporting the data as a VCD waveform file, a Python list, a
    CSV file, or a Verilog module.
    """

    def __init__(self, data, config, interface):
        self._data = data
        self._config = config
        self._interface = interface

    def get_trigger_location(self):
        """
        Gets the location of the trigger in the capture. This will match the
        value of "trigger_location" provided in the configuration file at the
        time of capture.
        """

        if "trigger_location" in self._config:
            return self._config["trigger_location"]

        else:
            return self._config["sample_depth"] // 2

    def get_trace(self, probe_name):
        """
        Gets the value of a single probe over the capture.
        """

        # Sum up the widths of all the probes below this one
        lower = 0
        for name, width in self._config["probes"].items():
            if name == probe_name:
                break

            lower += width

        # Add the width of the probe we'd like
        upper = lower + self._config["probes"][probe_name]

        total_probe_width = sum(self._config["probes"].values())
        binary = [f"{d:0{total_probe_width}b}" for d in self._data]
        return [int(b[lower:upper], 2) for b in binary]

    def export_csv(self, path):
        """
        Export the capture to a CSV file, containing the data of all probes in
        the core.
        """

        names = list(self._config["probes"].keys())
        values = [self.get_trace(n) for n in names]

        # Transpose list of lists so that data flows top-to-bottom instead of
        # left-to-right
        values_t = [list(x) for x in zip(*values)]

        import csv

        with open(path, "w") as f:
            writer = csv.writer(f)

            writer.writerow(names)
            writer.writerows(values_t)

    def export_vcd(self, path):
        """
        Export the capture to a VCD file, containing the data of all probes in
        the core.
        """

        from vcd import VCDWriter
        from datetime import datetime

        # Use the same datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")
        vcd_file = open(path, "w")

        # Compute the timescale from the frequency of the provided clock
        timescale_value = 0.5 / self._interface.get_frequency()
        timescale_scale = 0
        while timescale_value < 1.0:
            timescale_scale += 1
            timescale_value *= 10
        timescale = ["1 s", "100 ms", "10 ms", "1 ms", "100 us", "10 us", "1 us", "100 ns", "10 ns", "1 ns"][timescale_scale]

        with VCDWriter(vcd_file, timescale, timestamp, "manta") as writer:
            # Each probe has a name, width, and writer associated with it
            signals = []
            for name, width in self._config["probes"].items():
                signal = {
                    "name": name,
                    "width": width,
                    "data": self.get_trace(name),
                    "var": writer.register_var("manta", name, "wire", size=width),
                }
                signals.append(signal)

            clock = writer.register_var("manta", "clk", "wire", size=1)

            # Include a trigger signal such would be meaningful (ie, we didn't trigger immediately)
            if (
                "trigger_mode" not in self._config
                or self._config["trigger_mode"] == "single_shot"
            ):
                trigger = writer.register_var("manta", "trigger", "wire", size=1)

            # Add the data to each probe in the vcd file
            for timestamp in range(0, 2 * len(self._data)):
                # Calculate the nearest time step
                ts = round(timestamp * timescale_value)
                # Run the clock
                writer.change(clock, ts, timestamp % 2 == 0)

                # Set the trigger (if there is one)
                if (
                    "trigger_mode" not in self._config
                    or self._config["trigger_mode"] == "single_shot"
                ):
                    triggered = (timestamp // 2) >= self.get_trigger_location()
                    writer.change(trigger, ts, triggered)

                # Add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][timestamp // 2]

                    writer.change(var, ts, sample)

        vcd_file.close()

    def get_playback_module(self):
        """
        Returns an Amaranth module that will playback the captured data. This
        module is synthesizable, so it may be used in either simulation or
        on the FPGA directly by including it your build process.
        """

        return LogicAnalyzerPlayback(self._data, self._config)

    def export_playback_verilog(self, path):
        """
        Exports a Verilog module that will playback the captured data. This
        module is synthesizable, so it may be used in either simulation or
        on the FPGA directly by including it your build process.
        """

        lap = self.get_playback_module()
        from amaranth.back import verilog

        with open(path, "w") as f:
            f.write(
                verilog.convert(
                    lap,
                    name="logic_analyzer_playback",
                    ports=lap.get_top_level_ports(),
                    strip_internal_attrs=True,
                )
            )
