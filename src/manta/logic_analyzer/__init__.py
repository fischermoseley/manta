from amaranth import *
from warnings import warn
from ..utils import *
from .trigger_block import LogicAnalyzerTriggerBlock
from .fsm import LogicAnalyzerFSM
from .sample_mem import LogicAnalyzerSampleMemory
from .playback import LogicAnalyzerPlayback


class LogicAnalyzerCore(Elaboratable):
    """ """

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.check_config(config)

        # Bus Input
        self.addr_i = Signal(16)
        self.data_i = Signal(16)
        self.rw_i = Signal(1)
        self.valid_i = Signal(1)

        # Bus Output
        self.addr_o = Signal(16)
        self.data_o = Signal(16)
        self.rw_o = Signal(1)
        self.valid_o = Signal(1)

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

        # Top-Level Probes:
        for name, width in self.config["probes"].items():
            if hasattr(self, name):
                raise ValueError(
                    f"Unable to assign probe name '{name}' as it clashes with a reserved name in the backend. Please rename the probe."
                )

            setattr(self, name, Signal(width, name=name))

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
        if "sample_depth" not in config:
            raise ValueError("Logic Analyzer must have sample_depth specified.")

        if not isinstance(config["sample_depth"], int):
            raise ValueError("Logic Analyzer sample_depth must be an integer.")

        if config["sample_depth"] <= 0:
            raise ValueError("Logic Analyzer sample_depth must be positive.")

        # Check probes
        if "probes" not in config:
            raise ValueError("Logic Analyzer must have at least one probe specified.")

        if len(config["probes"]) == 0:
            raise ValueError("Logic Analyzer must have at least one probe specified.")

        for name, width in config["probes"].items():
            if width < 0:
                raise ValueError(f"Width of probe {name} must be positive.")

        # Check triggers
        if "triggers" not in config:
            raise ValueError("Logic Analyzer must have at least one trigger specified.")

        if len(config["triggers"]) == 0:
            raise ValueError("Logic Analyzer must have at least one trigger specified.")

        # Check trigger location
        if "trigger_location" in config:
            if not isinstance(config["trigger_location"], int):
                raise ValueError("Trigger location must be an integer.")

            if config["trigger_location"] < 0:
                raise ValueError("Trigger location must be positive.")

            if config["trigger_location"] > config["sample_depth"]:
                raise ValueError("Trigger location cannot exceed sample depth.")

        # Check trigger mode, if provided
        if "trigger_mode" in config:
            valid_modes = ["single_shot", "incremental", "immediate"]
            if config["trigger_mode"] not in valid_modes:
                raise ValueError(
                    f"Unrecognized trigger mode {config['trigger_mode']} provided."
                )

            if config["trigger_mode"] == "incremental":
                if "trigger_location" in config:
                    warn(
                        "Ignoring option 'trigger_location', as 'trigger_mode' is set to immediate, and there is no trigger condition to wait for."
                    )

        # Check triggers themselves
        for trigger in config["triggers"]:
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
                raise ValueError(f"Unable to interpret trigger condition '{trigger}'.")

            # Check probe names
            if components[0] not in config["probes"]:
                raise ValueError(f"Unknown probe name '{components[0]}' specified.")

    def elaborate(self, platform):
        m = Module()

        # Add submodules
        m.submodules["fsm"] = fsm = self.fsm
        m.submodules["sample_mem"] = sample_mem = self.sample_mem
        m.submodules["trig_blk"] = trig_blk = self.trig_blk

        # Concat all the probes together, and feed to input of sample memory
        # (it is necessary to reverse the order such that first probe occupies
        # the lowest location in memory)
        m.d.comb += sample_mem.user_data.eq(Cat(self.probes[::-1]))

        # Wire bus connections between internal modules
        m.d.comb += [
            # Bus Connections
            fsm.addr_i.eq(self.addr_i),
            fsm.data_i.eq(self.data_i),
            fsm.rw_i.eq(self.rw_i),
            fsm.valid_i.eq(self.valid_i),
            trig_blk.addr_i.eq(fsm.addr_o),
            trig_blk.data_i.eq(fsm.data_o),
            trig_blk.rw_i.eq(fsm.rw_o),
            trig_blk.valid_i.eq(fsm.valid_o),
            sample_mem.addr_i.eq(trig_blk.addr_o),
            sample_mem.data_i.eq(trig_blk.data_o),
            sample_mem.rw_i.eq(trig_blk.rw_o),
            sample_mem.valid_i.eq(trig_blk.valid_o),
            self.addr_o.eq(sample_mem.addr_o),
            self.data_o.eq(sample_mem.data_o),
            self.rw_o.eq(sample_mem.rw_o),
            self.valid_o.eq(sample_mem.valid_o),
            # Non-bus Connections
            fsm.trigger.eq(trig_blk.trig),
            sample_mem.user_addr.eq(fsm.r.write_pointer),
            sample_mem.user_we.eq(fsm.write_enable),
        ]

        return m

    def get_top_level_ports(self):
        return self.probes

    def get_max_addr(self):
        return self.sample_mem.get_max_addr()

    def capture(self, verbose=False):
        print_if_verbose = lambda x: print(x) if verbose else None

        # If core is not in IDLE state, request that it return to IDLE
        print_if_verbose(" -> Resetting core...")
        state = self.fsm.r.get_probe("state")
        if state != self.states["IDLE"]:
            self.fsm.r.set_probe("request_stop", 0)
            self.fsm.r.set_probe("request_stop", 1)
            self.fsm.r.set_probe("request_stop", 0)

            if self.fsm.r.get_probe("state") != self.fsm.states["IDLE"]:
                raise ValueError("Logic analyzer did not reset to IDLE state.")

        # Set triggers
        print_if_verbose(" -> Setting triggers...")
        self.trig_blk.set_triggers()

        # Set trigger mode, default to single-shot if user didn't specify a mode
        print_if_verbose(" -> Setting trigger mode...")
        if "trigger_mode" in self.config:
            self.fsm.r.set_probe("trigger_mode", self.config["trigger_mode"])

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
    def __init__(self, data, config):
        self.data = data
        self.config = config

    def get_trigger_location(self):
        return self.config["trigger_location"]

    def get_trace(self, probe_name):
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
            trigger = writer.register_var("manta", "trigger", "wire", size=1)

            # add the data to each probe in the vcd file
            for timestamp in range(0, 2 * len(self.data)):
                # run the clock
                writer.change(clock, timestamp, timestamp % 2 == 0)

                # set the trigger
                triggered = (timestamp // 2) >= self.get_trigger_loc()
                writer.change(trigger, timestamp, triggered)

                # add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][timestamp // 2]

                    writer.change(var, timestamp, sample)

        vcd_file.close()

    def export_playback_module(self):
        return LogicAnalyzerPlayback(self.data, self.config)

    def export_playback_verilog(self, path):
        lap = self.export_playback_module()
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
