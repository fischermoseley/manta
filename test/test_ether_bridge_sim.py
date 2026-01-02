# Test with 32-bit data/valid/ready/last interface for input, and one for output

from amaranth import *
from amaranth.lib.enum import IntEnum

from manta.ethernet import EthernetBridge
from manta.utils import *

# Actual testing below!

ether_bridge = EthernetBridge()

from random import randint


async def send_bytes(ctx, bytes):
    ctx.set(ether_bridge.ready_i, 1)
    ctx.set(ether_bridge.valid_i, 1)

    for i, byte in enumerate(bytes):
        ctx.set(ether_bridge.data_i, byte)
        ctx.set(ether_bridge.last_i, i == len(bytes) - 1)

        while not ctx.get(ether_bridge.ready_o):
            await ctx.tick()

        await ctx.tick()

    ctx.set(ether_bridge.data_i, 0)
    ctx.set(ether_bridge.last_i, 0)
    ctx.set(ether_bridge.valid_i, 0)
    await ctx.tick()


async def send_bytes_sporadic(ctx, bytes):
    ctx.set(ether_bridge.ready_i, 1)
    ctx.set(ether_bridge.valid_i, 1)

    for i, byte in enumerate(bytes):
        if randint(0, 1):
            ctx.set(ether_bridge.valid_i, 0)
            for _ in range(0, randint(1, 4)):
                await ctx.tick()

        ctx.set(ether_bridge.valid_i, 1)
        ctx.set(ether_bridge.data_i, byte)
        ctx.set(ether_bridge.last_i, i == len(bytes) - 1)

        while not ctx.get(ether_bridge.ready_o):
            await ctx.tick()

        await ctx.tick()

    ctx.set(ether_bridge.data_i, 0)
    ctx.set(ether_bridge.last_i, 0)
    ctx.set(ether_bridge.valid_i, 0)
    await ctx.tick()


# - type: 3 bits
# - seq_num: 13 bits
# - length (only if read request): 7 bits


async def send_write_request(ctx, seq_num, addr, write_data):
    await send_bytes_sporadic(
        ctx, [(seq_num << 3) | MessageTypes.WRITE_REQUEST, addr] + write_data
    )


async def send_read_request(ctx, seq_num, addr, read_length):
    await send_bytes_sporadic(
        ctx, [(read_length << 16) | (seq_num << 3) | MessageTypes.READ_REQUEST, addr]
    )


@simulate(ether_bridge)
async def test_ether_bridge(ctx):
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()

    # Send a read request with a bad sequence number
    # await send_read_request(ctx, seq_num=1, addr=0, read_length=1)
    # await ctx.tick()
    # await send_read_request(ctx, seq_num=1, addr=1, read_length=1)
    # await ctx.tick()

    # await send_write_request(ctx, seq_num=0, addr=0x1234_5678, write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222])
    # ctx.tick()

    await send_write_request(
        ctx,
        seq_num=0,
        addr=0x1234_5678,
        write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222, 0x3333_3333],
    )
    # await send_write_request(ctx, seq_num=4, addr=0x1234_5678, write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222])
    # await send_read_request(ctx, seq_num=0, addr=0x1234_5678, read_length=10)
    # await send_bytes(ctx, [0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567, 0x89AB_CDEF])
    ctx.tick()

    for _ in range(20):
        await ctx.tick()
