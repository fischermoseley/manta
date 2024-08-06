from manta.ethernet import UDPSourceBridge
from manta.utils import *

source_bridge = UDPSourceBridge()


@simulate(source_bridge)
async def test_normie_ops(ctx):
    ctx.set(source_bridge.data_i, 0)
    ctx.set(source_bridge.last_i, 0)
    ctx.set(source_bridge.valid_i, 0)
    await ctx.tick()

    ctx.set(source_bridge.data_i, 0x0000_0001)
    ctx.set(source_bridge.valid_i, 1)
    await ctx.tick()

    ctx.set(source_bridge.data_i, 0x1234_5678)
    await ctx.tick()

    ctx.set(source_bridge.valid_i, 0)
    await ctx.tick().repeat(2)

    ctx.set(source_bridge.valid_i, 1)
    ctx.set(source_bridge.data_i, 0x0000_0001)
    await ctx.tick()

    ctx.set(source_bridge.data_i, 0x90AB_CDEF)
    await ctx.tick()

    ctx.set(source_bridge.data_i, 0x0000_0000)
    await ctx.tick()

    ctx.set(source_bridge.data_i, 0x1234_5678)
    await ctx.tick()

    ctx.set(source_bridge.valid_i, 0)
    await ctx.tick().repeat(2)
