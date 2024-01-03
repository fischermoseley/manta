from amaranth.sim import Simulator
from manta.logic_analyzer_core import LogicAnalyzerCore
from manta.utils import *
from random import sample

config = {
    "type": "logic_analyzer",
    "sample_depth": 1024,
    "trigger_loc": 512,
    "probes": {"larry": 1, "curly": 3, "moe": 9},
    "triggers": ["moe RISING"],
}

la = LogicAnalyzerCore(config, base_addr=0, interface=None)

def print_data_at_addr(addr):
    # place read transaction on the bus
    yield la.addr_i.eq(addr)
    yield la.data_i.eq(0)
    yield la.rw_i.eq(0)
    yield la.valid_i.eq(1)
    yield
    yield la.addr_i.eq(0)
    yield la.valid_i.eq(0)

    # wait for output to be valid
    while not (yield la.valid_o):
        yield

    print(f"addr: {hex(addr)} data: {hex((yield la.data_o))}")


def set_logic_analyzer_register(name, data):
    addr = la.registers.mmap[f"{name}_buf"]["addrs"][0]

    yield from write_register(la, 0, 0)
    yield from write_register(la, addr, data)
    yield from write_register(la, 0, 1)
    yield from write_register(la, 0, 0)


def test_do_you_fucking_work():
    def testbench():
        # # ok nice what happens if we try to run the core, which includes:
        yield from set_logic_analyzer_register("request_stop", 1)
        yield from set_logic_analyzer_register("request_stop", 0)

        # setting triggers
        yield from set_logic_analyzer_register("curly_op", la.operations["EQ"])
        yield from set_logic_analyzer_register("curly_arg", 4)

        # setting trigger mode
        yield from set_logic_analyzer_register(
            "trigger_mode", 0
        )  # right now this is not actually respected...oops

        # setting trigger location
        yield from set_logic_analyzer_register("trigger_loc", 511)

        # starting capture
        yield from set_logic_analyzer_register("request_start", 1)
        yield from set_logic_analyzer_register("request_start", 0)

        # wait a few hundred clock cycles, see what happens
        for _ in range(700):
            yield

        # provide the trigger condition
        yield la.probe_signals["curly"]["top_level"].eq(4)

        for _ in range(700):
            yield

        # dump sample memory contents
        yield from write_register(la, 0, 0)
        yield from write_register(la, 0, 1)
        yield from write_register(la, 0, 0)

        for addr in range(la.get_max_addr()):
            yield from print_data_at_addr(addr)

    simulate(la, testbench, "la_core.vcd")
