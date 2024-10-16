import yaml
from amaranth import *

from manta.ethernet import EthernetInterface
from manta.io_core import IOCore
from manta.logic_analyzer import LogicAnalyzerCore
from manta.memory_core import MemoryCore
from manta.uart import UARTInterface
from manta.utils import *


class Manta(Elaboratable):
    def __init__(self):
        self._interface = None
        self.cores = CoreContainer(self)

    # This treats the `interface` attribute as a property, which allows the
    # setter to update the interfaces of all the cores in self.cores whenever
    # the user assigns to Manta's `interface` object.
    @property
    def interface(self):
        return self._interface

    @interface.setter
    def interface(self, value):
        self._interface = value
        for core in self.cores._cores.values():
            core.interface = value

    @classmethod
    def from_config(cls, config_path):
        # Load config from YAML
        extension = config_path.split(".")[-1]
        if extension not in ["yaml", "yml"]:
            raise ValueError(
                f"Configuration file {config_path} has unrecognized file type."
            )

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Validate config
        if "cores" not in config:
            raise ValueError("No cores specified in configuration file.")

        if not len(config["cores"]) > 0:
            raise ValueError("Must specify at least one core.")

        for name, attrs in config["cores"].items():
            # Make sure core type is specified
            if "type" not in attrs:
                raise ValueError(f"No type specified for core {name}.")

            if attrs["type"] not in ["logic_analyzer", "io", "memory"]:
                raise ValueError(f"Unrecognized core type specified for {name}.")

        # Make Manta object, and configure it
        manta = Manta()

        # Add interface
        if "uart" in config:
            manta.interface = UARTInterface.from_config(config["uart"])

        elif "ethernet" in config:
            manta.interface = EthernetInterface.from_config(config["ethernet"])

        # Add cores
        for name, attrs in config["cores"].items():
            if attrs["type"] == "io":
                core = IOCore.from_config(attrs)

            elif attrs["type"] == "logic_analyzer":
                core = LogicAnalyzerCore.from_config(attrs)

            elif attrs["type"] == "memory":
                core = MemoryCore.from_config(attrs)

            setattr(manta.cores, name, core)

        return manta

    def elaborate(self, platform):
        m = Module()

        # Add interface as submodule
        m.submodules.interface = self.interface

        # Add all cores as submodules
        for name, instance in self.cores._cores.items():
            m.submodules[name] = instance

        # Connect first/last cores to interface output/input respectively
        core_instances = list(self.cores._cores.values())
        first_core = core_instances[0]
        last_core = core_instances[-1]

        m.d.comb += first_core.bus_i.eq(self.interface.bus_o)
        m.d.comb += self.interface.bus_i.eq(last_core.bus_o)

        # Connect output of ith core to input of (i+1)th core
        for i in range(len(core_instances) - 1):
            ith_core = core_instances[i]
            i_plus_oneth_core = core_instances[i + 1]

            m.d.comb += i_plus_oneth_core.bus_i.eq(ith_core.bus_o)

        return m

    def get_top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """
        ports = self.interface.get_top_level_ports()

        for name, instance in self.cores._cores.items():
            ports += instance.top_level_ports

        return ports

    def generate_verilog(self, path, strip_internal_attrs=False):
        from amaranth.back import verilog

        output = verilog.convert(
            self,
            name="manta",
            ports=self.get_top_level_ports(),
            strip_internal_attrs=strip_internal_attrs,
        )

        # Below is a hack!
        # The Ethernet core is a Verilog snippet generated by LiteEth,
        # which gets appended to the Amaranth output such that everything
        # still lives within one file.

        # In the future this shouldn't be required once Amaranth SOC
        # launches, but until then, this is likely the simplest approach.
        if isinstance(self.interface, EthernetInterface):
            output += self.interface.generate_liteeth_core()

        with open(path, "w") as f:
            f.write(output)

    def export_config(self, path):
        "Export a YAML file containing all the configuration of the core"

        config = {}

        if self.cores._cores:
            config["cores"] = {}
            for name, instance in self.cores._cores.items():
                config["cores"][name] = instance.to_config()

        if self.interface:
            if isinstance(self.interface, UARTInterface):
                config["uart"] = self.interface.to_config()

            if isinstance(self.interface, EthernetInterface):
                config["ethernet"] = self.interface.to_config()

        import yaml

        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
