from amaranth import *
from warnings import warn
from .utils import *
from .io_core import IOCore
from .memory_core import ReadOnlyMemoryCore
from math import ceil, log2


class LogicAnalyzerCore(Elaboratable):
    """ """

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.base_addr = base_addr
        self.interface = interface

        self.check_config(config)

        # State Machine Values
        self.states = {
            "IDLE": 0,
            "MOVE_TO_POSITION": 1,
            "IN_POSITION": 2,
            "CAPTURING": 3,
            "CAPTURED": 4,
        }

        # Trigger Modes
        self.trigger_modes = {"SINGLE_SHOT": 0, "INCREMENTAL": 1, "IMMEDIATE": 2}

        # Trigger operations
        self.operations = {
            "DISABLE": 0,
            "RISING": 1,
            "FALLING": 2,
            "CHANGING": 3,
            "GT": 4,
            "LT": 5,
            "GEQ": 6,
            "LEQ": 7,
            "EQ": 8,
            "NEQ": 9,
        }

        self.registers = self.make_registers(self.base_addr)
        self.sample_mem = self.make_sample_mem(self.registers.max_addr)
        self.define_signals()

    def check_config(self, config):
        # Check for unrecognized options
        valid_options = [
            "type",
            "sample_depth",
            "probes",
            "triggers",
            "trigger_loc",
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
        if "trigger_loc" in config:
            if not isinstance(config["trigger_loc"], int):
                raise ValueError("Trigger location must be an integer.")

            if config["trigger_loc"] < 0:
                raise ValueError("Trigger location must be positive.")

            if config["trigger_loc"] > config["sample_depth"]:
                raise ValueError("Trigger location cannot exceed sample depth.")

        # Check trigger mode
        if "trigger_mode" in config:
            valid_modes = ["single_shot", "incremental", "immediate"]
            if config["trigger_mode"] not in valid_modes:
                raise ValueError(
                    f"Unrecognized trigger mode {config['trigger_mode']} provided."
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

    def define_signals(self):
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

        # Probes
        self.probe_signals = {}
        for name, width in self.config["probes"].items():
            self.probe_signals[name] = {
                "top_level": Signal(width),
                "prev": Signal(width),
                "trigger_arg": getattr(self.registers, f"{name}_arg"),
                "trigger_op": getattr(self.registers, f"{name}_op"),
                "triggered": Signal(1),
            }

        # Global trigger. High if any probe is triggered.
        self.trig = Signal(1)

    def make_registers(self, base_addr):
        # The logic analyzer uses an IO core to handle inputs to the FSM and trigger comparators
        register_config = {
            "inputs": {
                "state": 4,
                "read_pointer": ceil(log2(self.config["sample_depth"])),
                "write_pointer": ceil(log2(self.config["sample_depth"])),
            },
            "outputs": {
                "trigger_loc": ceil(log2(self.config["sample_depth"])),
                "trigger_mode": 2,
                "request_start": 1,
                "request_stop": 1,
            },
        }

        for name, width in self.config["probes"].items():
            register_config["outputs"][name + "_arg"] = width
            register_config["outputs"][name + "_op"] = 4

        return IOCore(register_config, base_addr, self.interface)

    def make_sample_mem(self, base_addr):
        sample_mem_config = {
            "width": sum(self.config["probes"].values()),
            "depth": self.config["sample_depth"],
        }

        return ReadOnlyMemoryCore(sample_mem_config, base_addr, self.interface)

    def run_triggers(self, m):
        # Run the trigger for each individual probe
        for name, attrs in self.probe_signals.items():
            top_level = attrs["top_level"]
            prev = attrs["prev"]
            trigger_arg = attrs["trigger_arg"]
            trigger_op = attrs["trigger_op"]
            triggered = attrs["triggered"]

            # Save the previous value to a register so we can do rising/falling edge detection later!
            m.d.sync += prev.eq(top_level)

            with m.If(trigger_op == self.operations["DISABLE"]):
                m.d.comb += triggered.eq(0)

            with m.Elif(trigger_op == self.operations["RISING"]):
                m.d.comb += triggered.eq((top_level) & (~prev))

            with m.Elif(trigger_op == self.operations["FALLING"]):
                m.d.comb += triggered.eq((~top_level) & (prev))

            with m.Elif(trigger_op == self.operations["CHANGING"]):
                m.d.comb += triggered.eq(top_level != prev)

            with m.Elif(trigger_op == self.operations["GT"]):
                m.d.comb += triggered.eq(top_level > trigger_arg)

            with m.Elif(trigger_op == self.operations["LT"]):
                m.d.comb += triggered.eq(top_level < trigger_arg)

            with m.Elif(trigger_op == self.operations["GEQ"]):
                m.d.comb += triggered.eq(top_level >= trigger_arg)

            with m.Elif(trigger_op == self.operations["LEQ"]):
                m.d.comb += triggered.eq(top_level <= trigger_arg)

            with m.Elif(trigger_op == self.operations["EQ"]):
                m.d.comb += triggered.eq(top_level == trigger_arg)

            with m.Elif(trigger_op == self.operations["NEQ"]):
                m.d.comb += triggered.eq(top_level != trigger_arg)

            with m.Else():
                m.d.comb += triggered.eq(0)

        # Combine all the triggers
        m.d.comb += self.trig.eq(
            Cat(attrs["triggered"] for attrs in self.probe_signals.values()).any()
        )

    def increment_mod_sample_depth(self, m, signal):
        # m.d.sync += signal.eq((signal + 1) % self.config["sample_depth"])

        with m.If(signal == self.config["sample_depth"] - 1):
            m.d.sync += signal.eq(0)

        with m.Else():
            m.d.sync += signal.eq(signal + 1)

    def run_state_machine(self, m):
        prev_request_start = Signal(1)
        prev_request_stop = Signal(1)

        request_start = self.registers.request_start
        request_stop = self.registers.request_stop
        trigger_mode = self.registers.trigger_mode
        trigger_loc = self.registers.trigger_loc
        state = self.registers.state
        rp = self.registers.read_pointer
        wp = self.registers.write_pointer
        we = self.sample_mem.user_we

        m.d.comb += self.sample_mem.user_addr.eq(wp)

        # Rising edge detection for start/stop requests
        m.d.sync += prev_request_start.eq(request_start)
        m.d.sync += prev_request_stop.eq(request_stop)

        with m.If(state == self.states["IDLE"]):
            m.d.sync += wp.eq(0)
            m.d.sync += rp.eq(0)
            m.d.sync += we.eq(0)

            with m.If((request_start) & (~prev_request_start)):
                m.d.sync += we.eq(1)
                with m.If(trigger_mode == self.trigger_modes["IMMEDIATE"]):
                    m.d.sync += state.eq(self.states["CAPTURING"])

                with m.Else():
                    with m.If(trigger_loc == 0):
                        m.d.sync += state.eq(self.states["IN_POSITION"])

                    with m.Else():
                        m.d.sync += state.eq(self.states["MOVE_TO_POSITION"])

                m.d.sync += state.eq(self.states["MOVE_TO_POSITION"])

        with m.Elif(state == self.states["MOVE_TO_POSITION"]):
            m.d.sync += wp.eq(wp + 1)

            with m.If(wp == trigger_loc):
                with m.If(self.trig):
                    m.d.sync += state.eq(self.states["CAPTURING"])

                with m.Else():
                    m.d.sync += state.eq(self.states["IN_POSITION"])
                    self.increment_mod_sample_depth(m, rp)

        with m.Elif(state == self.states["IN_POSITION"]):
            self.increment_mod_sample_depth(m, wp)

            with m.If(self.trig):
                m.d.sync += state.eq(self.states["CAPTURING"])

            with m.Else():
                self.increment_mod_sample_depth(m, rp)

        with m.Elif(state == self.states["CAPTURING"]):
            with m.If(wp == rp):
                m.d.sync += we.eq(0)
                m.d.sync += state.eq(self.states["CAPTURED"])

            with m.Else():
                self.increment_mod_sample_depth(m, wp)

        with m.If((request_stop) & (~prev_request_stop)):
            m.d.sync += state.eq(self.states["IDLE"])

    def elaborate(self, platform):
        m = Module()

        # Add registers and sample memory as submodules
        m.submodules["registers"] = self.registers
        m.submodules["sample_mem"] = self.sample_mem

        # Concat all the probes together, and feed to input of sample memory
        # (it is necessary to reverse the order such that first probe occupies
        # the lowest location in memory)
        m.d.comb += self.sample_mem.user_data.eq(
            Cat([p["top_level"] for p in self.probe_signals.values()][::-1])
        )

        self.run_state_machine(m)
        self.run_triggers(m)

        # Wire internal modules
        m.d.comb += [
            self.registers.addr_i.eq(self.addr_i),
            self.registers.data_i.eq(self.data_i),
            self.registers.rw_i.eq(self.rw_i),
            self.registers.valid_i.eq(self.valid_i),
            self.sample_mem.addr_i.eq(self.registers.addr_o),
            self.sample_mem.data_i.eq(self.registers.data_o),
            self.sample_mem.rw_i.eq(self.registers.rw_o),
            self.sample_mem.valid_i.eq(self.registers.valid_o),
            self.addr_o.eq(self.sample_mem.addr_o),
            self.data_o.eq(self.sample_mem.data_o),
            self.rw_o.eq(self.sample_mem.rw_o),
            self.valid_o.eq(self.sample_mem.valid_o),
        ]

        return m

    def get_top_level_ports(self):
        return [p["top_level"] for p in self.probe_signals.values()]

    def get_max_addr(self):
        return self.sample_mem.get_max_addr()

    def set_triggers(self):
        # reset all triggers to zero
        for name in self.probe_signals.keys():
            self.registers.set_probe(name + "_op", 0)
            self.registers.set_probe(name + "_arg", 0)

        # set triggers
        for trigger in self.config["triggers"]:
            components = trigger.strip().split(" ")

            # Handle triggers that don't need an argument
            if len(components) == 2:
                name, op = components
                self.registers.set_probe(name + "_op", self.operations[op])

            # Handle triggers that do need an argument
            elif len(components) == 3:
                name, op, arg = components
                self.registers.set_probe(name + "_op", self.operations[op])
                self.registers.set_probe(name + "_arg", int(arg))

    def capture(self, verbose=False):
        print_if_verbose = lambda x: print(x) if verbose else None

        # If core is not in IDLE state, request that it return to IDLE
        print_if_verbose(" -> Resetting core...")
        state = self.registers.get_probe("state")
        if state != self.states["IDLE"]:
            self.registers.set_probe("request_stop", 0)
            self.registers.set_probe("request_stop", 1)
            self.registers.set_probe("request_stop", 0)

            if self.registers.get_probe("state") != self.states["IDLE"]:
                raise ValueError("Logic analyzer did not reset to IDLE state.")

        # Set triggers
        print_if_verbose(" -> Setting triggers...")
        self.set_triggers()

        # Set trigger mode, default to single-shot if user didn't specify a mode
        print_if_verbose(" -> Setting trigger mode...")
        if "trigger_mode" in self.config:
            self.registers.set_probe("trigger_mode", self.config["trigger_mode"])

        else:
            self.registers.set_probe("trigger_mode", self.trigger_modes["SINGLE_SHOT"])

        # Set trigger location
        print_if_verbose(" -> Setting trigger location...")
        self.registers.set_probe("trigger_loc", self.config["trigger_loc"])

        # Send a start request to the state machine
        print_if_verbose(" -> Starting capture...")
        self.registers.set_probe("request_start", 1)
        self.registers.set_probe("request_start", 0)

        # Poll the state machine's state, and wait for the capture to complete
        print_if_verbose(" -> Waiting for capture to complete...")
        while self.registers.get_probe("state") != self.states["CAPTURED"]:
            pass

        # Read out the entirety of the sample memory
        print_if_verbose(" -> Reading sample memory contents...")
        addrs = list(range(self.config["sample_depth"]))
        raw_capture = self.sample_mem.read_from_user_addr(addrs)

        # Revolve the memory around the read_pointer, such that all the beginning
        # of the caputure is at the first element
        print_if_verbose(" -> Checking read pointer and revolving memory...")
        read_pointer = self.registers.get_probe("read_pointer")

        data = raw_capture[read_pointer:] + raw_capture[:read_pointer]
        return LogicAnalyzerCapture(data, self.config)


class LogicAnalyzerCapture:
    def __init__(self, data, config):
        self.data = data
        self.config = config

    def get_trigger_loc(self):
        return self.config["trigger_loc"]

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


class LogicAnalyzerPlayback(Elaboratable):
    def __init__(self, data, config):
        self.data = data
        self.config = config

        # State Machine
        self.start = Signal(1)
        self.valid = Signal(1)

        # Top-Level Probe signals
        self.top_level_probes = {}
        for name, width in self.config["probes"].items():
            self.top_level_probes[name] = Signal(width, name=name)

        # Instantiate memory
        self.mem = Memory(
            depth=self.config["sample_depth"],
            width=sum(self.config["probes"].values()),
            init=self.data,
        )

        self.read_port = self.mem.read_port()

    def elaborate(self, platform):
        m = Module()
        m.submodules["mem"] = self.mem

        m.d.comb += self.read_port.en.eq(1)

        # State Machine
        busy = Signal(1)
        with m.If(~busy):
            with m.If(self.start):
                m.d.sync += busy.eq(1)
                # m.d.sync += self.read_port.addr.eq(1)

        with m.Else():
            with m.If(self.read_port.addr == self.config["sample_depth"] - 1):
                m.d.sync += busy.eq(0)
                m.d.sync += self.read_port.addr.eq(0)

            with m.Else():
                m.d.sync += self.read_port.addr.eq(self.read_port.addr + 1)

        # Pipeline to accomodate for the 2-cycle latency in the RAM
        m.d.sync += self.valid.eq(busy)

        # Assign the probe values by part-selecting from the data port
        lower = 0
        for name, width in reversed(self.config["probes"].items()):
            signal = self.top_level_probes[name]

            # Set output probe to zero if we're not
            with m.If(self.valid):
                m.d.comb += signal.eq(self.read_port.data[lower : lower + width])

            with m.Else():
                m.d.comb += signal.eq(0)

            lower += width

        return m

    def get_top_level_ports(self):
        return [self.start, self.valid] + list(self.top_level_probes.values())
