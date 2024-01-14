from amaranth import *
from warnings import warn
from ..utils import *
from .trigger_block import LogicAnalyzerTriggerBlock
from .fsm import LogicAnalyzerFSM
from .sample_mem import LogicAnalyzerSampleMemory
from .playback import LogicAnalyzerPlayback


class LogicAnalyzerCore(Elaboratable):
    """A logic analzyer, implemented in the FPGA fabric. Connects to the rest of the cores
    over Manta's internal bus, and may be operated from a user's machine through the Python API.

    Parameters:
    ----------
    config : dict
        Configuration options. This is taken from the section of Manta's configuration YAML that
        describes the core.

    base_addr : int
        Where to place the core in Manta's internal memory map. This determines the beginning of
        the core's address space. The end of the core's address space may be obtained by calling
        the get_max_addr() method.

    interface : UARTInterface or EthernetInterface
        The interface used to communicate with the core.

    Attributes:
    ----------
    None


    """

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.check_config(config)

        # Bus Input/Output
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        self.probes = [
            Signal(width, name=name) for name, width in self.config["probes"].items()
        ]

        # Submodules
        self.fsm = LogicAnalyzerFSM(self.config, base_addr, interface)
        self.trig_blk = LogicAnalyzerTriggerBlock(
            self.probes, self.fsm.get_max_addr() + 1, interface
        )
        self.sample_mem = LogicAnalyzerSampleMemory(
            self.config, self.trig_blk.get_max_addr() + 1, interface
        )

    def check_config(self, config):
        # Check for unrecognized options
        valid_options = [
            "type",
            "sample_depth",
            "probes",
            "triggers",
            "trigger_location",
            "trigger_mode",
        ]
        for option in config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in Logic Analyzer.")

        # Check sample depth is provided and positive
        sample_depth = config.get("sample_depth")
        if not sample_depth:
            raise ValueError("Logic Analyzer must have sample_depth specified.")

        if not isinstance(sample_depth, int) or sample_depth <= 0:
            raise ValueError("Logic Analyzer sample_depth must be a positive integer.")

        # Check probes
        if "probes" not in config or len(config["probes"]) == 0:
            raise ValueError("Logic Analyzer must have at least one probe specified.")

        for name, width in config["probes"].items():
            if width < 0:
                raise ValueError(f"Width of probe {name} must be positive.")

        # Check trigger mode, if provided
        trigger_mode = config.get("trigger_mode")
        valid_modes = ["single_shot", "incremental", "immediate"]
        if trigger_mode and trigger_mode not in valid_modes:
            raise ValueError(
                f"Unrecognized trigger mode {config['trigger_mode']} provided."
            )

        # Check triggers
        if (trigger_mode) and (trigger_mode != "immediate"):
            if ("triggers" not in config) or (config["triggers"] == 0):
                raise ValueError(
                    "Logic Analyzer must have at least one trigger specified."
                )

        # Check trigger location
        trigger_location = config.get("trigger_location")
        if trigger_location:
            if not isinstance(trigger_location, int) or trigger_location < 0:
                raise ValueError("Trigger location must be a positive integer.")

            if trigger_location > config["sample_depth"]:
                raise ValueError("Trigger location cannot exceed sample depth.")

            if trigger_mode == "immediate":
                warn(
                    "Ignoring option 'trigger_location', as 'trigger_mode' is set to immediate, and there is no trigger condition to wait for."
                )

        # Check triggers themselves
        if trigger_mode == "immediate":
            if "triggers" in config:
                warn(
                    "Ignoring triggers as 'trigger_mode' is set to immediate, and there are no triggers to specify."
                )

        else:
            if ("triggers" not in config) or (len(config["triggers"]) == 0):
                raise ValueError("At least one trigger must be specified.")

            for trigger in config.get("triggers"):
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
                if components[0] not in config["probes"]:
                    raise ValueError(f"Unknown probe name '{components[0]}' specified.")

    def elaborate(self, platform):
        m = Module()

        # Add submodules
        m.submodules.fsm = fsm = self.fsm
        m.submodules.sample_mem = sample_mem = self.sample_mem
        m.submodules.trig_blk = trig_blk = self.trig_blk

        # Concat all the probes together, and feed to input of sample memory
        # (it is necessary to reverse the order such that first probe occupies
        # the lowest location in memory)
        m.d.comb += sample_mem.user_data.eq(Cat(self.probes[::-1]))

        # Wire bus connections between internal modules
        m.d.comb += [
            # Bus Connections
            fsm.bus_i.eq(self.bus_i),
            trig_blk.bus_i.eq(self.fsm.bus_o),
            sample_mem.bus_i.eq(trig_blk.bus_o),
            self.bus_o.eq(sample_mem.bus_o),
            # Non-bus Connections
            fsm.trigger.eq(trig_blk.trig),
            sample_mem.user_addr.eq(fsm.r.write_pointer),
            sample_mem.user_we.eq(fsm.write_enable),
        ]

        return m

    def get_top_level_ports(self):
        return self.probes

    def get_probe(self, name):
        for p in self.probes:
            if p.name == name:
                return p

        raise ValueError(f"Probe '{name}' not found in Logic Analyzer core.")

    def get_max_addr(self):
        return self.sample_mem.get_max_addr()

    def capture(self, verbose=False):
        """Perform a capture, recording the state of all input probes to the FPGA's memory, and
        then reading that out on the host.

        Parameters:
        ----------
        verbose : bool
            Whether or not to print the status of the capture to stdout as it progresses.
            Defaults to False.

        Returns:
        ----------
        An instance of LogicAnalyzerCapture.
        """
        print_if_verbose = lambda x: print(x) if verbose else None

        # If core is not in IDLE state, request that it return to IDLE
        print_if_verbose(" -> Resetting core...")
        state = self.fsm.r.get_probe("state")
        if state != self.fsm.states["IDLE"]:
            self.fsm.r.set_probe("request_start", 0)
            self.fsm.r.set_probe("request_stop", 0)
            self.fsm.r.set_probe("request_stop", 1)
            self.fsm.r.set_probe("request_stop", 0)

            if self.fsm.r.get_probe("state") != self.fsm.states["IDLE"]:
                raise ValueError("Logic analyzer did not reset to IDLE state.")

        # Set triggers
        print_if_verbose(" -> Setting triggers...")
        self.trig_blk.clear_triggers()

        if self.config["trigger_mode"] != "immediate":
            self.trig_blk.set_triggers(self.config)

        # Set trigger mode, default to single-shot if user didn't specify a mode
        print_if_verbose(" -> Setting trigger mode...")
        if "trigger_mode" in self.config:
            mode = self.config["trigger_mode"].upper()
            self.fsm.r.set_probe("trigger_mode", self.fsm.trigger_modes[mode])

        else:
            self.fsm.r.set_probe("trigger_mode", self.fsm.trigger_modes["SINGLE_SHOT"])

        # Set trigger location
        print_if_verbose(" -> Setting trigger location...")
        if "trigger_location" in self.config:
            self.fsm.r.set_probe("trigger_location", self.config["trigger_location"])

        else:
            self.fsm.r.set_probe("trigger_location", self.config["sample_depth"] // 2)

        # Send a start request to the state machine
        print_if_verbose(" -> Starting capture...")
        self.fsm.r.set_probe("request_start", 0)
        self.fsm.r.set_probe("request_start", 1)
        self.fsm.r.set_probe("request_start", 0)

        # Poll the state machine's state, and wait for the capture to complete
        print_if_verbose(" -> Waiting for capture to complete...")
        while self.fsm.r.get_probe("state") != self.fsm.states["CAPTURED"]:
            pass

        # Read out the entirety of the sample memory
        print_if_verbose(" -> Reading sample memory contents...")
        addrs = list(range(self.config["sample_depth"]))
        raw_capture = self.sample_mem.read_from_user_addr(addrs)

        # Revolve the memory around the read_pointer, such that all the beginning
        # of the caputure is at the first element
        print_if_verbose(" -> Checking read pointer and revolving memory...")
        read_pointer = self.fsm.r.get_probe("read_pointer")

        data = raw_capture[read_pointer:] + raw_capture[:read_pointer]
        return LogicAnalyzerCapture(data, self.config)


class LogicAnalyzerCapture:
    """A container for the data collected during a capture from a LogicAnalyzerCore. Contains
    methods for exporting the data as a VCD waveform file, or as a Verilog module for playing
    back captured data in simulation/synthesis.

    Parameters:
    ----------
    data : list[int]
        The raw captured data taken by the LogicAnalyzerCore. This consists of the values of
        all the input probes concatenated together at every timestep.

    config : dict
        The configuration of the LogicAnalyzerCore that took this capture.
    """

    def __init__(self, data, config):
        self.data = data
        self.config = config

    def get_trigger_location(self):
        """Gets the location of the trigger in the capture. This will match the value of
        "trigger_location" provided in the configuration file at the time of capture.

        Parameters:
        ----------
        None

        Returns:
        ----------
        The trigger location as an `int`.
        """
        return self.config["trigger_location"]

    def get_trace(self, probe_name):
        """Gets the value of a single probe over the capture.

        Parameters:
        ----------
        probe_name : int
            The name of the probe in the LogicAnalyzer Core. This must match the name provided
            in the configuration file.

        Returns:
        ----------
        The value of the probe at every timestep in the capture, as a list of integers.
        """

        # sum up the widths of all the probes below this one
        lower = 0
        for name, width in self.config["probes"].items():
            if name == probe_name:
                break

            lower += width

        # add the width of the probe we'd like
        upper = lower + self.config["probes"][probe_name]

        total_probe_width = sum(self.config["probes"].values())
        binary = [f"{d:0{total_probe_width}b}" for d in self.data]
        return [int(b[lower:upper], 2) for b in binary]

    def export_vcd(self, path):
        """Export the capture to a VCD file, containing the data of all probes in the core.

        Parameters:
        ----------
        path : str
            The path of the output file, including the ".vcd" file extension.

        Returns:
        ----------
        None

        """

        from vcd import VCDWriter
        from datetime import datetime

        # Use the same datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")
        vcd_file = open(path, "w")

        with VCDWriter(vcd_file, "10 ns", timestamp, "manta") as writer:
            # each probe has a name, width, and writer associated with it
            signals = []
            for name, width in self.config["probes"].items():
                signal = {
                    "name": name,
                    "width": width,
                    "data": self.get_trace(name),
                    "var": writer.register_var("manta", name, "wire", size=width),
                }
                signals.append(signal)

            clock = writer.register_var("manta", "clk", "wire", size=1)

            # include a trigger signal such would be meaningful (ie, we didn't trigger immediately)
            if self.config["trigger_mode"] != "immediate":
                trigger = writer.register_var("manta", "trigger", "wire", size=1)

            # add the data to each probe in the vcd file
            for timestamp in range(0, 2 * len(self.data)):
                # run the clock
                writer.change(clock, timestamp, timestamp % 2 == 0)

                # set the trigger (if there is one)
                if self.config["trigger_mode"] != "immediate":
                    triggered = (timestamp // 2) >= self.get_trigger_location()
                    writer.change(trigger, timestamp, triggered)

                # add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][timestamp // 2]

                    writer.change(var, timestamp, sample)

        vcd_file.close()

    def get_playback_module(self):
        """Gets an Amaranth module that will playback the captured data. This module is
        synthesizable, so it may be used in either simulation or synthesis.

        Parameters:
        ----------
        None

        Returns:
        ----------
        An instance of LogicAnalyzerPlayback, which is a synthesizable Amaranth module.
        """
        return LogicAnalyzerPlayback(self.data, self.config)

    def export_playback_verilog(self, path):
        """Exports a Verilog module that will playback the captured data. This module is
        synthesizable, so it may be used in either simulation or synthesis.

        Parameters:
        ----------
        path : str
            The path of the output file, including the ".v" file extension.

        Returns:
        ----------
        None
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
