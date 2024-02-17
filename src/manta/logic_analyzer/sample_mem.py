from amaranth import *
from manta.memory_core import ReadOnlyMemoryCore


class LogicAnalyzerSampleMemory(ReadOnlyMemoryCore):
    """
    A module that wraps a ReadOnlyMemoryCore, using the config from a LogicAnalyzerCore
    to determine the parameters with which to instantiate the core.
    """

    def __init__(self, config, base_addr, interface):
        width = sum(config["probes"].values())
        depth = config["sample_depth"]
        mem_config = {"width": width, "depth": depth}

        super().__init__(mem_config, base_addr, interface)
