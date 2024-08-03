from amaranth import *
from manta.uart import UARTInterface
from manta.ethernet import EthernetInterface
from manta.io_core import IOCore
from manta.memory_core import MemoryCore
from manta.logic_analyzer import LogicAnalyzerCore
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

    # def __init__(self, config):
    #     # Load config from either a configuration file or a dictionary.
    #     # Users primarily use the config file, but the dictionary is
    #     # included for internal tests.

    #     if isinstance(config, str):
    #         self._config = self._read_config_file(config)

    #     if isinstance(config, dict):
    #         self._config = config

    #     self._check_config()

    #     self._get_interface()
    #     self._get_cores()
    #     self._add_friendly_core_names()

    # def _read_config_file(self, path):
    #     """
    #     Takes a path to configuration file, and return the configuration as a
    #     python dictionary.
    #     """

    #     extension = path.split(".")[-1]

    #     if "json" in extension:
    #         import json
    #         with open(path, "r") as f:
    #             return json.load(f)

    #     elif "yaml" in extension or "yml" in extension:
    #         import yaml
    #         with open(path, "r") as f:
    #             return yaml.safe_load(f)

    #     else:
    #         raise ValueError("Unable to recognize configuration file extension.")

    # def _check_config(self):
    #     if "cores" not in self._config:
    #         raise ValueError("No cores specified in configuration file.")

    #     if not len(self._config["cores"]) > 0:
    #         raise ValueError("Must specify at least one core.")

    #     for name, attrs in self._config["cores"].items():
    #         # Make sure core type is specified
    #         if "type" not in attrs:
    #             raise ValueError(f"No type specified for core {name}.")

    #         if attrs["type"] not in ["logic_analyzer", "io", "memory"]:
    #             raise ValueError(f"Unrecognized core type specified for {name}.")

    # def _get_interface(self):
    #     """
    #     Returns an instance of an interface object (UARTInterface or
    #     EthernetInterface) configured with the parameters in the
    #     config file.
    #     """
    #     if "uart" in self._config:
    #         self.interface = UARTInterface.from_config(self._config["uart"])

    #     elif "ethernet" in self._config:
    #         self.interface = EthernetInterface(self._config["ethernet"])

    #     else:
    #         raise ValueError("No recognized interface specified.")

    # def _get_cores(self):
    #     """
    #     Creates instances of the cores (IOCore, LogicAnalyzerCore, MemoryCore)
    #     specified in the user's configuration, and returns them as a list.
    #     """

    #     self._cores = {}
    #     base_addr = 0
    #     for name, attrs in self._config["cores"].items():
    #         if attrs["type"] == "io":
    #             core = IOCore.from_config(attrs, base_addr, self.interface)

    #         elif attrs["type"] == "logic_analyzer":
    #             core = LogicAnalyzerCore(attrs, base_addr, self.interface)

    #         elif attrs["type"] == "memory":
    #             core = MemoryCore.from_config(attrs, base_addr, self.interface)

    #         # Make sure we're not out of address space
    #         if core.max_addr > (2**16) - 1:
    #             raise ValueError(
    #                 f"Ran out of address space to allocate to core {name}."
    #             )

    #         # Make the next core's base address start one address after the previous one's
    #         base_addr = core.max_addr + 1
    #         self._cores[name] = core

    # def _add_friendly_core_names(self):
    #     """
    #     Add cores to the instance under a friendly name - ie, a core named `my_core` belonging
    #     to a Manta instance `m` could be obtained with `m.cores["my_core"]`, but this allows
    #     it to be obtained with `m.my_core`. Which is way nicer.
    #     """

    #     for name, instance in self._cores.items():
    #         if not hasattr(self, name):
    #             setattr(self, name, instance)

    #         else:
    #             raise ValueError(
    #                 "Cannot add object to Manta instance - name is already taken!"
    #             )

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
