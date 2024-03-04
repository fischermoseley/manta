from amaranth.sim import Simulator
from manta.logic_analyzer import LogicAnalyzerCore
from manta.logic_analyzer.trigger_block import Operations
from manta.utils import *
from random import sample

config = {
    "type": "logic_analyzer",
    "sample_depth": 1024,
    "trigger_location": 512,
    "probes": {"larry": 1, "curly": 3, "moe": 9},
    "triggers": ["moe RISING"],
}

la = LogicAnalyzerCore(config, base_addr=0, interface=None)


def print_data_at_addr(addr):
    # place read transaction on the bus
    yield la.bus_i.addr.eq(addr)
    yield la.bus_i.data.eq(0)
    yield la.bus_i.rw.eq(0)
    yield la.bus_i.valid.eq(1)
    yield
    yield la.bus_i.addr.eq(0)
    yield la.bus_i.valid.eq(0)

    # wait for output to be valid
    while not (yield la.bus_o.valid):
        yield

    print(f"addr: {hex(addr)} data: {hex((yield la.bus_o.data))}")


def set_fsm_register(name, data):
    addr = la._fsm.registers._memory_map[name]["addrs"][0]
    strobe_addr = la._fsm.registers._base_addr

    yield from write_register(la, strobe_addr, 0)
    yield from write_register(la, addr, data)
    yield from write_register(la, strobe_addr, 1)
    yield from write_register(la, strobe_addr, 0)


def set_trig_blk_register(name, data):
    addr = la._trig_blk.registers._memory_map[name]["addrs"][0]
    strobe_addr = la._trig_blk.registers._base_addr

    yield from write_register(la, strobe_addr, 0)
    yield from write_register(la, addr, data)
    yield from write_register(la, strobe_addr, 1)
    yield from write_register(la, strobe_addr, 0)


def set_probe(name, value):
    probe = None
    for p in la._probes:
        if p.name == name:
            probe = p

    yield probe.eq(value)


@simulate(la)
def test_single_shot_capture():
    # # ok nice what happens if we try to run the core, which includes:
    yield from set_fsm_register("request_stop", 1)
    yield from set_fsm_register("request_stop", 0)

    # setting triggers
    yield from set_trig_blk_register("curly_op", Operations.EQ)
    yield from set_trig_blk_register("curly_arg", 4)

    # setting trigger mode
    yield from set_fsm_register("trigger_mode", 0)

    # setting trigger location
    yield from set_fsm_register("trigger_location", 511)

    # starting capture
    yield from set_fsm_register("request_start", 1)
    yield from set_fsm_register("request_start", 0)

    # wait a few hundred clock cycles, see what happens
    for _ in range(700):
        yield

    # provide the trigger condition
    yield from set_probe("curly", 4)

    for _ in range(700):
        yield

    # dump sample memory contents
    yield from write_register(la, 0, 0)
    yield from write_register(la, 0, 1)
    yield from write_register(la, 0, 0)

    for addr in range(la.max_addr):
        yield from print_data_at_addr(addr)
