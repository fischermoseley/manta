from amaranth.sim import Simulator
from manta.logic_analyzer import *
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


def test_signals_reset_correctly():
    def testbench():
        # Make sure pointers and write enable reset to zero
        for sig in [fsm.r.write_pointer, fsm.r.read_pointer, fsm.write_enable]:
            if (yield sig) != 0:
                raise ValueError

        # Make sure state resets to IDLE
        if (yield fsm.r.state != States.IDLE):
            raise ValueError

    simulate(fsm, testbench)


def test_single_shot_no_wait_for_trigger():
    def testbench():
        # Configure and start FSM
        yield fsm.trigger.eq(1)
        yield fsm.r.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
        yield fsm.r.trigger_location.eq(4)
        yield fsm.r.request_start.eq(1)

        # Wait until write_enable is asserted
        while not (yield fsm.write_enable):
            yield

        # Wait 8 clock cycles for capture to complete
        for i in range(8):
            # Make sure that read_pointer does not increase
            if (yield fsm.r.read_pointer) != 0:
                raise ValueError

            # Make sure that write_pointer increases by one each cycle
            if (yield fsm.r.write_pointer) != i:
                raise ValueError

            yield

        # Wait one clock cycle (to let BRAM contents cycle in)
        yield

        # Check that write_pointer points to the end of memory
        if (yield fsm.r.write_pointer) != 7:
            raise ValueError

        # Check that state is CAPTURED
        if (yield fsm.r.state) != States.CAPTURED:
            raise ValueError

    simulate(fsm, testbench, "single_shot_no_wait_for_trigger.vcd")


def test_single_shot_wait_for_trigger():
    def testbench():
        # Configure and start FSM
        yield fsm.r.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
        yield fsm.r.trigger_location.eq(4)
        yield fsm.r.request_start.eq(1)
        yield

        # Check that write_enable is asserted on the same edge as request_start
        if not (yield fsm.write_enable):
            raise ValueError

        # Wait 4 clock cycles to get to IN_POSITION
        for i in range(4):
            rp = yield fsm.r.read_pointer
            wp = yield fsm.r.write_pointer

            # Make sure that read_pointer does not increase
            if rp != 0:
                raise ValueError

            # Make sure that write_pointer increases by one each cycle
            if wp != i:
                raise ValueError

            yield

        # Wait a few cycles before triggering:
        for _ in range(10):
            if (rp + 3) % fsm.config["sample_depth"] != wp:
                raise ValueError

            yield

        # Provide the trigger, and check that the capture completes 4 cycles later
        yield fsm.trigger.eq(1)
        yield

        rp_start = yield fsm.r.read_pointer
        for i in range(4):
            rp = yield fsm.r.read_pointer
            wp = yield fsm.r.write_pointer

            if rp != rp_start:
                raise ValueError

            if (rp_start + 4 + i) % fsm.config["sample_depth"] != wp:
                raise ValueError

            yield

        # Wait one clock cycle (to let BRAM contents cycle in)
        yield

        # Check that write_pointer points to the end of memory
        rp = yield fsm.r.read_pointer
        wp = yield fsm.r.write_pointer
        if (wp + 1) % fsm.config["sample_depth"] != rp:
            raise ValueError

        # Check that state is CAPTURED
        if (yield fsm.r.state) != States.CAPTURED:
            raise ValueError

    simulate(fsm, testbench, "single_shot_wait_for_trigger.vcd")


def test_immediate():
    def testbench():
        # Configure and start FSM
        yield fsm.r.trigger_mode.eq(TriggerModes.IMMEDIATE)
        yield fsm.r.request_start.eq(1)
        yield

        # Check that write_enable is asserted on the same edge as request_start
        if not (yield fsm.write_enable):
            raise ValueError

        for i in range(fsm.config["sample_depth"]):
            rp = yield fsm.r.read_pointer
            wp = yield fsm.r.write_pointer

            if rp != 0:
                raise ValueError

            if wp != i:
                raise ValueError

            yield

        # Wait one clock cycle (to let BRAM contents cycle in)
        yield

        # Check that write_pointer points to the end of memory
        rp = yield fsm.r.read_pointer
        wp = yield fsm.r.write_pointer
        if rp != 0:
            raise ValueError
        if wp != 7:
            raise ValueError

        # Check that state is CAPTURED
        if (yield fsm.r.state) != States.CAPTURED:
            raise ValueError

    simulate(fsm, testbench, "immediate.vcd")


def test_incremental():
    def testbench():
        # Configure and start FSM
        yield fsm.r.trigger_mode.eq(TriggerModes.INCREMENTAL)
        yield fsm.r.request_start.eq(1)
        yield

        # Check that write_enable is asserted on the same edge as request_start
        # if not (yield fsm.write_enable):
        #     raise ValueError

        for _ in range(10):
            for _ in range(3):
                yield

            yield fsm.trigger.eq(1)
            yield
            yield fsm.trigger.eq(0)
            yield

        # # Check that state is CAPTURED
        # if (yield fsm.r.state) != States.CAPTURED:
        #     raise ValueError

    simulate(fsm, testbench, "incremental.vcd")


def test_single_shot_write_enable():
    def testbench():
        # Configure FSM
        yield fsm.r.trigger_mode.eq(TriggerModes.SINGLE_SHOT)
        yield fsm.r.trigger_location.eq(4)
        yield

        # Make sure write is not enabled before starting the FSM
        if (yield fsm.write_enable):
            raise ValueError

        # Start the FSM, ensure write enable is asserted throughout the capture
        yield fsm.r.request_start.eq(1)
        yield

        for _ in range(fsm.config["sample_depth"]):
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

    simulate(fsm, testbench, "single_shot_write_enable.vcd")


def test_immediate_write_enable():
    def testbench():
        # Configure FSM
        yield fsm.r.trigger_mode.eq(TriggerModes.IMMEDIATE)
        yield

        # Make sure write is not enabled before starting the FSM
        if (yield fsm.write_enable):
            raise ValueError

        # Start the FSM, ensure write enable is asserted throughout the capture
        yield fsm.r.request_start.eq(1)
        yield

        for _ in range(fsm.config["sample_depth"]):
            if not (yield fsm.write_enable):
                raise ValueError

            yield

        # Make sure write_enable is deasserted after
        if (yield fsm.write_enable):
            raise ValueError

    simulate(fsm, testbench, "immediate_write_enable.vcd")
