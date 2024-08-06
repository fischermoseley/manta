from manta.cli import main
from manta.ethernet import EthernetInterface
from manta.io_core import IOCore
from manta.logic_analyzer import LogicAnalyzerCore, TriggerModes
from manta.manta import Manta
from manta.memory_core import MemoryCore
from manta.uart import UARTInterface

__all__ = [
    "Manta",
    "UARTInterface",
    "EthernetInterface",
    "LogicAnalyzerCore",
    "TriggerModes",
    "IOCore",
    "MemoryCore",
]

if __name__ == "__main__":
    main()
