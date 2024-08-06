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

    More information available in the online documentation at:
    https://fischermoseley.github.io/manta/logic_analyzer_core/
    """

    def __init__(self, sample_depth, probes):
        self._sample_depth = sample_depth
        self._probes = probes
        self.trigger_location = sample_depth // 2
        self.trigger_mode = TriggerModes.SINGLE_SHOT
        self.triggers = []

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
        return {
            "type": "logic_analyzer",
            "sample_depth": self._sample_depth,
            "trigger_location": self.trigger_location,
            "probes": {p.name: len(p) for p in self._probes},
            "triggers": self.triggers,
        }

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

        # Check trigger mode, if provided
        trigger_mode = config.get("trigger_mode")
        valid_modes = ["single_shot", "incremental", "immediate"]
        if trigger_mode and trigger_mode not in valid_modes:
            raise ValueError(
                f"Unrecognized trigger mode {config['trigger_mode']} provided."
            )

        # Check triggers
        if trigger_mode and trigger_mode != "immediate":
            if "triggers" not in config or config["triggers"] == 0:
                raise ValueError(
                    "Logic Analyzer must have at least one trigger specified if not running in immediate mode."
                )

        # Check trigger location
        trigger_location = config.get("trigger_location")
        if trigger_location:
            if not isinstance(trigger_location, int) or trigger_location < 0:
                raise ValueError("Trigger location must be a positive integer.")

            if trigger_location >= config["sample_depth"]:
                raise ValueError("Trigger location must be less than sample depth.")

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

        # Checks complete, create LogicAnalyzerCore
        probes = [Signal(width, name=name) for name, width in config["probes"].items()]

        return cls(config["sample_depth"], probes)

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

    def capture(self):
        """
        Performs a capture, recording the state of all input probes to the
        FPGA's memory, and then returns that as a LogicAnalyzerCapture class
        on the host.
        """

        print(" -> Resetting core...")
        self._fsm.stop_capture()

        print(" -> Setting triggers...")
        self._trig_blk.set_triggers(self.triggers)

        print(" -> Setting trigger mode...")
        self._fsm.write_register("trigger_mode", self.trigger_mode)

        print(" -> Setting trigger location...")
        self._fsm.write_register("trigger_location", self.trigger_location)

        print(" -> Starting capture...")
        self._fsm.start_capture()

        print(" -> Waiting for capture to complete...")
        self._fsm.wait_for_capture()

        print(" -> Reading sample memory contents...")
        addrs = list(range(self._sample_depth))
        raw_capture = self._sample_mem.read(addrs)

        # Revolve the memory around the read_pointer, such that all the beginning
        # of the caputure is at the first element
        print(" -> Checking read pointer and revolving memory...")
        read_pointer = self._fsm.read_register("read_pointer")

        data = raw_capture[read_pointer:] + raw_capture[:read_pointer]
        return LogicAnalyzerCapture(
            self._probes, self.trigger_location, self.trigger_mode, data
        )
