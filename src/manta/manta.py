from amaranth import *
from warnings import warn
from .uart import UARTInterface

# from .ethernet import EthernetInterface
from .io_core import IOCore
from .memory_core import ReadOnlyMemoryCore
from .logic_analyzer import LogicAnalyzerCore


class Manta(Elaboratable):
    def __init__(self, config):
        # load config from either a configuration file or a dictionary. Users primarily use the
        # config file, but the dictionary is included for internal tests.

        if isinstance(config, str):
            self.config = self.read_config_file(config)

        if isinstance(config, dict):
            self.config = config

        self.check_config()

        self.interface = self.get_interface()
        self.cores = self.get_cores()
        self.add_friendly_core_names()

    def read_config_file(self, path):
        """
        Take path to configuration file, and retun the configuration as a python list/dict object.
        """

        extension = path.split(".")[-1]

        if "json" in extension:
            with open(path, "r") as f:
                import json

                return json.load(f)

        elif "yaml" in extension or "yml" in extension:
            with open(path, "r") as f:
                import yaml

                return yaml.safe_load(f)

        else:
            raise ValueError("Unable to recognize configuration file extension.")

    def check_config(self):
        if "cores" not in self.config:
            raise ValueError("No cores specified in configuration file.")

        if not len(self.config["cores"]) > 0:
            raise ValueError("Must specify at least one core.")

        for name, attrs in self.config["cores"].items():
            # make sure core type is specified
            if "type" not in attrs:
                raise ValueError(f"No type specified for core {name}.")

            if attrs["type"] not in ["logic_analyzer", "io", "memory_read_only"]:
                raise ValueError(f"Unrecognized core type specified for {name}.")

    def get_interface(self):
        if "uart" in self.config:
            return UARTInterface(self.config["uart"])

        elif "ethernet" in self.config:
            return EthernetInterface(self.config["ethernet"])

        else:
            raise ValueError("Unrecognized interface specified.")

    def get_cores(self):
        """ """

        cores = {}
        base_addr = 0
        for name, attrs in self.config["cores"].items():
            if attrs["type"] == "io":
                core = IOCore(attrs, base_addr, self.interface)

            elif attrs["type"] == "logic_analyzer":
                core = LogicAnalyzerCore(attrs, base_addr, self.interface)

            elif attrs["type"] == "memory_read_only":
                core = ReadOnlyMemoryCore(attrs, base_addr, self.interface)

            # make sure we're not out of address space
            if core.get_max_addr() > (2**16) - 1:
                raise ValueError(
                    f"Ran out of address space to allocate to core {name}."
                )

            # Make the next core's base address start one address after the previous one's
            base_addr = core.get_max_addr() + 1
            cores[name] = core

        return cores

    def add_friendly_core_names(self):
        """
        Add cores to the instance under a friendly name - ie, a core named `my_core` belonging
        to a Manta instance `m` could be obtained with `m.cores["my_core"]`, but this allows
        it to be obtained with `m.my_core`. Which is way nicer.
        """

        for name, instance in self.cores.items():
            if not hasattr(self, name):
                setattr(self, name, instance)

            else:
                raise ValueError(
                    "Cannot add object to Manta instance - name is already taken!"
                )

    def elaborate(self, platform):
        # make a module object
        # add all the submodules
        # connect them together, which consists of:
        # connect interface to first core
        # connect cores to each other
        # connect interface to last core

        m = Module()

        # Add interface as submodule
        m.submodules["interface"] = self.interface

        # Add all cores as submodules
        for name, instance in self.cores.items():
            m.submodules[name] = instance

        # Connect first/last cores to interface output/input respectively
        core_instances = list(self.cores.values())
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
        ports = self.interface.get_top_level_ports()

        for name, instance in self.cores.items():
            ports += instance.get_top_level_ports()

        return ports
