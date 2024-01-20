from amaranth.sim import Simulator
from manta.logic_analyzer import LogicAnalyzerFSM
from manta.utils import *

"""
what do we want this to do?

we want to run a capture in single shot mode, immediate mode, and incremental mode


single-shot case:
- exactly the right number of samples are taken
- we only start taking samples once captured

immediate case:
- exactly the right number of samples are taken
- we only start taking samples once captured

incremental case:
- exactly the right number of samples are taken
- we only take samples when trig is asserted

"""
config = {"sample_depth": 8}
fsm = LogicAnalyzerFSM(config, base_addr=0, interface=None)


def set_fsm_register(name, data):
    addr = fsm.r.mmap[f"{name}_buf"]["addrs"][0]
    strobe_addr = fsm.r.base_addr

    yield from write_register(fsm, strobe_addr, 0)
    yield from write_register(fsm, addr, data)
    yield from write_register(fsm, strobe_addr, 1)
    yield from write_register(fsm, strobe_addr, 0)


def test_single_shot_always_trigger():
    def testbench():
        if (yield fsm.r.state != fsm.states["IDLE"]):
            raise ValueError

        yield fsm.trigger.eq(1)
        yield from set_fsm_register("trigger_mode", fsm.trigger_modes["SINGLE_SHOT"])
        yield from set_fsm_register("trigger_location", 4)
        yield from set_fsm_register("request_start", 1)
        yield from set_fsm_register("request_start", 0)

        for _ in range(100):
            yield

    simulate(fsm, testbench, "single_shot_always_trigger.vcd")


def test_single_shot_wait_to_trigger():
    def testbench():
        if (yield fsm.r.state != fsm.states["IDLE"]):
            raise ValueError

        yield from set_fsm_register("trigger_mode", fsm.trigger_modes["SINGLE_SHOT"])
        yield from set_fsm_register("trigger_location", 4)
        yield from set_fsm_register("request_start", 1)
        yield from set_fsm_register("request_start", 0)

        for _ in range(8):
            yield

        yield fsm.trigger.eq(1)

        for _ in range(100):
            yield

    simulate(fsm, testbench, "single_shot_wait_to_trigger.vcd")
