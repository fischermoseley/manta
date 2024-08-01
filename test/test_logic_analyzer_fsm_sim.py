from manta.logic_analyzer import TriggerModes
from manta.logic_analyzer.fsm import LogicAnalyzerFSM, States
from manta.utils import *

sample_depth = 8
fsm = LogicAnalyzerFSM(sample_depth, base_addr=0, interface=None)
_ = fsm.max_addr


@simulate(fsm)
async def test_signals_reset_correctly(ctx):
    # Make sure pointers and write enable reset to zero
    for sig in [fsm.write_pointer, fsm.read_pointer, fsm.write_enable]:
        if ctx.get(sig) != 0:
            raise ValueError

    # Make sure state resets to IDLE
    if ctx.get(fsm.state) != States.IDLE:
        raise ValueError


@simulate(fsm)
async def test_single_shot_no_wait_for_trigger(ctx):
    # Configure and start FSM
    ctx.set(fsm.trigger, 1)
    ctx.set(fsm.trigger_mode, TriggerModes.SINGLE_SHOT)
    ctx.set(fsm.trigger_location, 4)
    ctx.set(fsm.request_start, 1)

    # Wait until write_enable is asserted
    while not ctx.get(fsm.write_enable):
        await ctx.tick()

    # Wait 8 clock cycles for capture to complete
    for i in range(8):
        # Make sure that read_pointer does not increase
        if ctx.get(fsm.read_pointer) != 0:
            raise ValueError

        # Make sure that write_pointer increases by one each cycle
        if ctx.get(fsm.write_pointer) != i:
            raise ValueError

        await ctx.tick()

    # Wait one clock cycle (to let BRAM contents cycle in)
    await ctx.tick()

    # Check that write_pointer points to the end of memory
    if ctx.get(fsm.write_pointer) != 7:
        raise ValueError

    # Check that state is CAPTURED
    if ctx.get(fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
async def test_single_shot_wait_for_trigger(ctx):
    # Configure and start FSM
    ctx.set(fsm.trigger_mode, TriggerModes.SINGLE_SHOT)
    ctx.set(fsm.trigger_location, 4)
    ctx.set(fsm.request_start, 1)
    await ctx.tick()

    # Check that write_enable is asserted a cycle after request_start
    if not ctx.get(fsm.write_enable):
        raise ValueError

    # Wait 4 clock cycles to get to IN_POSITION
    for i in range(4):
        rp = ctx.get(fsm.read_pointer)
        wp = ctx.get(fsm.write_pointer)

        # Make sure that read_pointer does not increase
        if rp != 0:
            raise ValueError

        # Make sure that write_pointer increases by one each cycle
        if wp != i:
            raise ValueError

        await ctx.tick()

    # Wait a few cycles before triggering
    for _ in range(10):
        await ctx.tick()

    # Provide the trigger, and check that the capture completes 4 cycles later
    ctx.set(fsm.trigger, 1)
    await ctx.tick()

    for i in range(4):
        await ctx.tick()

    # Wait one clock cycle (to let BRAM contents cycle in)
    await ctx.tick()

    # Check that write_pointer points to the end of memory
    rp = ctx.get(fsm.read_pointer)
    wp = ctx.get(fsm.write_pointer)
    if (wp + 1) % sample_depth != rp:
        raise ValueError

    # Check that state is CAPTURED
    if ctx.get(fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
async def test_immediate(ctx):
    # Configure and start FSM
    ctx.set(fsm.trigger_mode, TriggerModes.IMMEDIATE)
    ctx.set(fsm.request_start, 1)
    await ctx.tick()

    # Check that write_enable is asserted a cycle after request_start
    if not ctx.get(fsm.write_enable):
        raise ValueError

    for i in range(sample_depth):
        rp = ctx.get(fsm.read_pointer)
        wp = ctx.get(fsm.write_pointer)

        if rp != 0:
            raise ValueError

        if wp != i:
            raise ValueError

        await ctx.tick()

    # Wait one clock cycle (to let BRAM contents cycle in)
    await ctx.tick()

    # Check that write_pointer points to the end of memory
    rp = ctx.get(fsm.read_pointer)
    wp = ctx.get(fsm.write_pointer)
    if rp != 0:
        raise ValueError
    if wp != 7:
        raise ValueError

    # Check that state is CAPTURED
    if ctx.get(fsm.state) != States.CAPTURED:
        raise ValueError


@simulate(fsm)
async def test_incremental(ctx):
    # Configure and start FSM
    ctx.set(fsm.trigger_mode, TriggerModes.INCREMENTAL)
    ctx.set(fsm.request_start, 1)
    await ctx.tick()

    # Check that write_enable is asserted on the same edge as request_start
    if not ctx.get(fsm.write_enable):
        raise ValueError

    for _ in range(10):
        await ctx.tick().repeat(3)

        ctx.set(fsm.trigger, 1)
        await ctx.tick()

        ctx.set(fsm.trigger, 0)
        await ctx.tick()

    # Check that state is CAPTURED
    if ctx.get(fsm.state) != States.CAPTURED:
        raise ValueError


# @simulate(fsm)
# async def test_single_shot_write_enable(ctx):
#     # Configure FSM
#     ctx.set(fsm.trigger_mode, TriggerModes.SINGLE_SHOT)
#     ctx.set(fsm.trigger_location, 4)
#     await ctx.tick()

#     # Make sure write is not enabled before starting the FSM
#     if ctx.get(fsm.write_enable):
#         raise ValueError

#     # Start the FSM, ensure write enable is asserted throughout the capture
#     ctx.set(fsm.request_start, 1)
#     await ctx.tick()
#     await ctx.tick()

#     for _ in range(config["sample_depth"]):
#         if not ctx.get(fsm.write_enable):
#             raise ValueError

#         await ctx.tick()

#     ctx.set(fsm.trigger, 1)
#     await ctx.tick()

#     for _ in range(4):
#         if not ctx.get(fsm.write_enable):
#             raise ValueError

#         await ctx.tick()

#     # Make sure write_enable is deasserted after
#     if ctx.get(fsm.write_enable):
#         raise ValueError


@simulate(fsm)
async def test_immediate_write_enable(ctx):
    # Configure FSM
    ctx.set(fsm.trigger_mode, TriggerModes.IMMEDIATE)
    await ctx.tick()

    # Make sure write is not enabled before starting the FSM
    if ctx.get(fsm.write_enable):
        raise ValueError

    # Start the FSM, ensure write enable is asserted throughout the capture
    ctx.set(fsm.request_start, 1)
    await ctx.tick()

    for _ in range(sample_depth):
        if not ctx.get(fsm.write_enable):
            raise ValueError

        await ctx.tick()

    # Make sure write_enable is deasserted after
    if ctx.get(fsm.write_enable):
        raise ValueError
