from amaranth import *

from manta.logic_analyzer import LogicAnalyzerCore
from manta.logic_analyzer.trigger_block import Operations
from manta.utils import *

larry = Signal(1)
curly = Signal(3)
moe = Signal(9)

la = LogicAnalyzerCore(1024, [larry, curly, moe])
la.base_addr = 0
_ = la.max_addr


async def print_data_at_addr(ctx, addr):
    # place read transaction on the bus
    ctx.set(la.bus_i.addr, addr)
    ctx.set(la.bus_i.data, 0)
    ctx.set(la.bus_i.rw, 0)
    ctx.set(la.bus_i.valid, True)

    await ctx.tick()

    ctx.set(la.bus_i.addr, 0)
    ctx.set(la.bus_i.valid, 0)

    # wait for output to be valid
    while not ctx.get(la.bus_o.valid):
        await ctx.tick()

    print(f"addr: {hex(addr)} data: {hex(ctx.get(la.bus_o.data))}")


async def set_fsm_register(ctx, name, data):
    addr = la._fsm.registers._memory_map[name]["addrs"][0]
    strobe_addr = la._fsm.registers.base_addr

    await write_register(la, ctx, strobe_addr, 0)
    await write_register(la, ctx, addr, data)
    await write_register(la, ctx, strobe_addr, 1)
    await write_register(la, ctx, strobe_addr, 0)


async def set_trig_blk_register(ctx, name, data):
    addr = la._trig_blk.registers._memory_map[name]["addrs"][0]
    strobe_addr = la._trig_blk.registers.base_addr

    await write_register(la, ctx, strobe_addr, 0)
    await write_register(la, ctx, addr, data)
    await write_register(la, ctx, strobe_addr, 1)
    await write_register(la, ctx, strobe_addr, 0)


async def set_probe(ctx, name, value):
    probe = None
    for p in la._probes:
        if p.name == name:
            probe = p

    ctx.set(probe, value)


@simulate(la)
async def test_single_shot_capture(ctx):
    # request FSM to stop
    await set_fsm_register(ctx, "request_stop", 1)
    await set_fsm_register(ctx, "request_stop", 0)

    # setting triggers
    await set_trig_blk_register(ctx, "curly_op", Operations.EQ)
    await set_trig_blk_register(ctx, "curly_arg", 4)

    # setting trigger mode
    await set_fsm_register(ctx, "trigger_mode", 0)

    # setting trigger location
    await set_fsm_register(ctx, "trigger_location", 511)

    # starting capture
    await set_fsm_register(ctx, "request_start", 1)
    await set_fsm_register(ctx, "request_start", 0)

    # wait a few hundred clock cycles, see what happens
    await ctx.tick().repeat(700)

    # provide the trigger condition
    await set_probe(ctx, "curly", 4)

    await ctx.tick().repeat(700)

    # dump sample memory contents
    await write_register(la, ctx, 0, 0)
    await write_register(la, ctx, 0, 1)
    await write_register(la, ctx, 0, 0)

    for addr in range(la.max_addr):
        await print_data_at_addr(ctx, addr)
