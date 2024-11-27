from amaranth import *

from manta.logic_analyzer.capture import LogicAnalyzerCapture
from manta.logic_analyzer.fsm import LogicAnalyzerFSM, TriggerModes
from manta.logic_analyzer.trigger_block import LogicAnalyzerTriggerBlock
from manta.memory_core import MemoryCore
from manta.utils import *


class LogicAnalyzerCore(MantaCore):
    """
    A module for generating a logic analyzer on the FPGA, with configurable
    triggers, trigger position, and trigger modes.

    Provides methods for generating synthesizable logic for the FPGA, as well
    as methods for reading and writing the value of a register.
    """

    def __init__(self, sample_depth, probes):
        """
        Create a Logic Analyzer Core with the given probes and sample depth.

        This function is the main mechanism for configuring a Logic Analyzer in
        an Amaranth-native design.

        Args:
            sample_depth (int):  The number of samples saved in the capture. A
                larger sample depth will use more FPGA resources, but will show
                what the probes are doing over a longer time interval.

            probes (List[Signal]): The signals in your logic that the Logic
                Analyzer connects to. Each probe is specified with a name and
                a width.
        """

        self._sample_depth = sample_depth
        self._probes = probes

        self._trigger_location = sample_depth // 2
        self._trigger_mode = TriggerModes.IMMEDIATE
        self._triggers = []

        # Bus Input/Output
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

    @property
    def max_addr(self):
        self.define_submodules()
        return self._sample_mem.max_addr

    @property
    def top_level_ports(self):
        return self._probes

    def to_config(self):
        config = {
            "type": "logic_analyzer",
            "sample_depth": self._sample_depth,
            "probes": {p.name: len(p) for p in self._probes},
        }

        if self._trigger_mode == TriggerModes.INCREMENTAL:
            config["trigger_mode"] = self._trigger_mode.name.lower()
            config["triggers"] = self._triggers

        elif self._trigger_mode == TriggerModes.SINGLE_SHOT:
            config["trigger_mode"] = self._trigger_mode.name.lower()
            config["triggers"] = self._triggers
            config["trigger_location"] = self._trigger_location

        return config

    @classmethod
    def from_config(cls, config):
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

        # Check triggers are specified with strings
        triggers = config.get("triggers", [])
        for trigger in triggers:
            if not isinstance(trigger, str):
                raise ValueError("Trigger must be specified with a string.")

        # Convert triggers to list
        triggers = [t.strip().split(" ") for t in triggers]

        # Checks and formatting complete, create LogicAnalyzerCore
        probes = [Signal(width, name=name) for name, width in config["probes"].items()]
        core = cls(sample_depth, probes)

        # If any trigger-related configuration was provided, set the triggers with it
        keys = ["trigger_mode", "triggers", "trigger_location"]
        if any([key in config for key in keys]):
            core.set_triggers(
                trigger_mode=config.get("trigger_mode"),
                triggers=triggers,
                trigger_location=config.get("trigger_location"),
            )

        return core

    def define_submodules(self):
        self._fsm = LogicAnalyzerFSM(
            sample_depth=self._sample_depth,
            base_addr=self.base_addr,
            interface=self.interface,
        )

        self._trig_blk = LogicAnalyzerTriggerBlock(
            probes=self._probes,
            base_addr=self._fsm.max_addr + 1,
            interface=self.interface,
        )

        self._sample_mem = MemoryCore(
            mode="fpga_to_host",
            width=sum([len(p) for p in self._probes]),
            depth=self._sample_depth,
        )
        self._sample_mem.base_addr = self._trig_blk.max_addr + 1
        self._sample_mem.interface = self.interface

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

    def _validate_triggers(self, triggers):
        """
        This function takes a list of lists, where each sublist may have two or
        three entries.
        """
        if not triggers:
            raise ValueError("At least one trigger must be specified.")

        for trigger in triggers:
            # Check two-token triggers
            if len(trigger) == 2:
                name, operation = trigger

                # Check name
                if name not in [p.name for p in self._probes]:
                    raise ValueError(f"Unknown probe name '{name}' specified.")

                # Check operation
                if operation not in ["DISABLE", "RISING", "FALLING", "CHANGING"]:
                    raise ValueError(
                        f"Unable to interpret trigger condition '{trigger}'."
                    )

            # Check three-token triggers
            elif len(trigger) == 3:
                name, operation, argument = trigger

                # Check name
                if name not in [p.name for p in self._probes]:
                    raise ValueError(f"Unknown probe name '{name}' specified.")

                # Check operation
                if operation not in ["GT", "LT", "GEQ", "LEQ", "EQ", "NEQ"]:
                    raise ValueError(
                        f"Unable to interpret trigger condition '{trigger}'."
                    )

            else:
                raise ValueError(f"Unable to interpret trigger condition '{trigger}'.")

    def set_triggers(self, trigger_mode=None, triggers=None, trigger_location=None):
        """
        Args:
            trigger_mode (TriggerMode | str):

            triggers (Optional[Sequence[Sequence[str | int]]]):

            trigger_location (Optional[int]):
        """
        # Obtain trigger mode
        if isinstance(trigger_mode, TriggerModes):
            mode = trigger_mode

        elif isinstance(trigger_mode, str):
            mode = TriggerModes[trigger_mode.upper()]

        else:
            raise ValueError(f"Unrecognized trigger mode {trigger_mode} provided.")

        # Perform checks based on trigger mode
        if mode == TriggerModes.IMMEDIATE:
            # Warn on triggers
            if triggers:
                warn("Ignoring provided triggers as trigger mode is set to Immediate.")

            # Warn on trigger location
            if trigger_location:
                warn(
                    "Ignoring provided trigger_location as trigger mode is set to Immediate."
                )

            self._trigger_mode = mode
            self._triggers = []
            self._trigger_location = self._sample_depth // 2

        elif mode == TriggerModes.INCREMENTAL:
            # Warn on trigger location
            if trigger_location:
                warn(
                    "Ignoring provided trigger_location as trigger mode is set to Incremental."
                )

            # Validate triggers
            self._validate_triggers(triggers)

            self._trigger_mode = mode
            self._triggers = triggers
            self._trigger_location = self._sample_depth // 2

        elif mode == TriggerModes.SINGLE_SHOT:
            # Validate trigger location, if provided
            if trigger_location:
                if not 0 <= trigger_location < self._sample_depth:
                    raise ValueError(
                        "Trigger location must be a positive integer between 0 and sample_depth."
                    )

            # Validate triggers
            self._validate_triggers(triggers)

            self.trigger_mode = mode
            self._triggers = triggers
            self._trigger_location = trigger_location or self._sample_depth // 2

    def capture(self):
        """
        Performs a capture, recording the state of all probes to memory.

        Returns:
            capture (LogicAnalyzerCapture): A LogicAnalyzerCapture object
                containing the capture and its metadata.
        """

        print(" -> Resetting core...")
        self._fsm.stop_capture()

        print(" -> Setting triggers...")
        self._trig_blk.set_triggers(self._triggers)

        print(" -> Setting trigger mode...")
        self._fsm.write_register("trigger_mode", self._trigger_mode)

        print(" -> Setting trigger location...")
        self._fsm.write_register("trigger_location", self._trigger_location)

        print(" -> Starting capture...")
        self._fsm.start_capture()

        print(" -> Waiting for capture to complete...")
        self._fsm.wait_for_capture()

        print(" -> Reading sample memory contents...")
        addrs = list(range(self._sample_depth))
        raw_capture = self._sample_mem.read(addrs)

        # Revolve the memory around the read_pointer, such that all the beginning
        # of the capture is at the first element
        print(" -> Checking read pointer and revolving memory...")
        read_pointer = self._fsm.read_register("read_pointer")

        data = raw_capture[read_pointer:] + raw_capture[:read_pointer]
        return LogicAnalyzerCapture(
            self._probes,
            self._trigger_location,
            self._trigger_mode,
            data,
            self.interface,
        )
