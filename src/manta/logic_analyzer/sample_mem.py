from amaranth import *
from ..memory_core import ReadOnlyMemoryCore


class LogicAnalyzerSampleMemory(ReadOnlyMemoryCore):
    def __init__(self, config, base_addr, interface):
        width = sum(config["probes"].values())
        depth = config["sample_depth"]
        mem_config = {"width": width, "depth": depth}

        super().__init__(mem_config, base_addr, interface)
