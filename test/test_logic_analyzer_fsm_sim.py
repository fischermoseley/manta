from amaranth.sim import Simulator
from manta.logic_analyzer import *
from manta.utils import *

config = {"sample_depth": 8}
fsm = LogicAnalyzerFSM(config, base_addr=0, interface=None)


@simulate(fsm)
def test_signals_reset_correctly():
    # Make sure pointers and write enable reset to zero
    for sig in [fsm.write_pointer, fsm.read_pointer, fsm.write_enable]:
        if (yield sig) != 0:
            raise ValueError

    # Make sure state resets to IDLE
    if (yield fsm.state != States.IDLE):
        raise ValueError


@simulate(fsm)
def test_single_shot_no_wait_for_trigger():
    # Configure and start FSM
    yield fsm.trigger.eq(1)
    yield fsm.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
    yield fsm.trigger_location.eq(4)
    yield fsm.request_start.eq(1)

    # Wait until write_enable is asserted
    while not (yield fsm.write_enable):
        yield

    # Wait 8 clock cycles for capture to complete
    for i in range(8):
        # Make sure that read_pointer does not increase
        if (yield fsm.read_pointer) != 0:
            raise ValueError

        # Make sure that write_pointer increases by one each cycle
        if (yield fsm.write_pointer) != i:
            raise ValueError

        yield

    # Wait one clock cycle (to let BRAM contents cycle in)
    yield

    # Check that write_pointer points to the end of memory
    if (yield fsm.write_pointer) != 7:
        raise ValueError

    # Check that state is CAPTURED
    if (yield fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
def test_single_shot_wait_for_trigger():
    # Configure and start FSM
    yield fsm.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
    yield fsm.trigger_location.eq(4)
    yield fsm.request_start.eq(1)
    yield
    yield

    # Check that write_enable is asserted a cycle after request_start
    if not (yield fsm.write_enable):
        raise ValueError

    # Wait 4 clock cycles to get to IN_POSITION
    for i in range(4):
        rp = yield fsm.read_pointer
        wp = yield fsm.write_pointer

        # Make sure that read_pointer does not increase
        if rp != 0:
            raise ValueError

        # Make sure that write_pointer increases by one each cycle
        if wp != i:
            raise ValueError

        yield

    # Wait a few cycles before triggering
    for _ in range(10):
        yield

    # Provide the trigger, and check that the capture completes 4 cycles later
    yield fsm.trigger.eq(1)
    yield

    for i in range(4):
        yield

    # Wait one clock cycle (to let BRAM contents cycle in)
    yield

    # Check that write_pointer points to the end of memory
    rp = yield fsm.read_pointer
    wp = yield fsm.write_pointer
    if (wp + 1) % config["sample_depth"] != rp:
        raise ValueError

    # Check that state is CAPTURED
    if (yield fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
def test_immediate():
    # Configure and start FSM
    yield fsm.trigger_mode.eq(TriggerModes.IMMEDIATE)
    yield fsm.request_start.eq(1)
    yield
    yield

    # Check that write_enable is asserted a cycle after request_start
    if not (yield fsm.write_enable):
        raise ValueError

    for i in range(config["sample_depth"]):
        rp = yield fsm.read_pointer
        wp = yield fsm.write_pointer

        if rp != 0:
            raise ValueError

        if wp != i:
            raise ValueError

        yield

    # Wait one clock cycle (to let BRAM contents cycle in)
    yield

    # Check that write_pointer points to the end of memory
    rp = yield fsm.read_pointer
    wp = yield fsm.write_pointer
    if rp != 0:
        raise ValueError
    if wp != 7:
        raise ValueError

    # Check that state is CAPTURED
    if (yield fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
def test_incremental():
    # Configure and start FSM
    yield fsm.trigger_mode.eq(TriggerModes.INCREMENTAL)
    yield fsm.request_start.eq(1)
    yield
    yield

    # Check that write_enable is asserted on the same edge as request_start
    if not (yield fsm.write_enable):
        raise ValueError

    for _ in range(10):
        for _ in range(3):
            yield

        yield fsm.trigger.eq(1)
        yield
        yield fsm.trigger.eq(0)
        yield

    # Check that state is CAPTURED
    if (yield fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
def test_single_shot_write_enable():
    # Configure FSM
    yield fsm.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
    yield fsm.trigger_location.eq(4)
    yield

    # Make sure write is not enabled before starting the FSM
    if (yield fsm.write_enable):
        raise ValueError

    # Start the FSM, ensure write enable is asserted throughout the capture
    yield fsm.request_start.eq(1)
    yield
    yield

    for _ in range(config["sample_depth"]):
        if not (yield fsm.write_enable):
            raise ValueError

        yield

    yield fsm.trigger.eq(1)
    yield

    for _ in range(4):
        if not (yield fsm.write_enable):
            raise ValueError

        yield

    # Make sure write_enable is deasserted after
    if (yield fsm.write_enable):
        raise ValueError


@simulate(fsm)
def test_immediate_write_enable():
    # Configure FSM
    yield fsm.trigger_mode.eq(TriggerModes.IMMEDIATE)
    yield

    # Make sure write is not enabled before starting the FSM
    if (yield fsm.write_enable):
        raise ValueError

    # Start the FSM, ensure write enable is asserted throughout the capture
    yield fsm.request_start.eq(1)
    yield
    yield

    for _ in range(config["sample_depth"]):
        if not (yield fsm.write_enable):
            raise ValueError

        yield

    # Make sure write_enable is deasserted after
    if (yield fsm.write_enable):
        raise ValueError
