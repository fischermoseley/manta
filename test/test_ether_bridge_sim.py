# Test with 32-bit data/valid/ready/last interface for input, and one for output

from amaranth import *
from amaranth.lib.enum import IntEnum

from manta import *
from manta.ethernet import EthernetBridge
from manta.utils import *

# Actual testing below!

ether_bridge = EthernetBridge()

from random import randint


async def send_bytes(ctx, module, bytes):
    ctx.set(module.ready_i, 1)
    ctx.set(module.valid_i, 1)

    for i, byte in enumerate(bytes):
        ctx.set(module.data_i, byte)
        ctx.set(module.last_i, i == len(bytes) - 1)

        while not ctx.get(module.ready_o):
            await ctx.tick()

        await ctx.tick()

    ctx.set(module.data_i, 0)
    ctx.set(module.last_i, 0)
    ctx.set(module.valid_i, 0)
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


async def send_write_request(ctx, module, seq_num, addr, write_data):
    await send_bytes(ctx, module, [(seq_num << 3) | MessageTypes.WRITE_REQUEST, addr] + write_data)


async def send_read_request(ctx, module, seq_num, addr, read_length):
    await send_bytes(
        ctx,
        module,
        [(read_length << 16) | (seq_num << 3) | MessageTypes.READ_REQUEST, addr],
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

    # await send_write_request(
    #     ctx,
    #     seq_num=0,
    #     addr=0x1234_5678,
    #     write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222, 0x3333_3333],
    # )
    # await send_write_request(ctx, seq_num=4, addr=0x1234_5678, write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222])
    await send_read_request(ctx, ether_bridge, seq_num=0, addr=0x1234_5678, read_length=1)
    # await send_bytes(ctx, [0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567, 0x89AB_CDEF])
    ctx.tick()

    for _ in range(20):
        await ctx.tick()


# Test with a memory core attached!
class EthernetBridgePlusMemoryCore(Elaboratable):
    def __init__(self):
        self.data_i = Signal(32)
        self.valid_i = Signal()
        self.last_i = Signal()
        self.ready_o = Signal()

        self.data_o = Signal(32)
        self.valid_o = Signal()
        self.last_o = Signal()
        self.ready_i = Signal()

    def elaborate(self, platform):
        m = Module()
        m.submodules.bridge = bridge = EthernetBridge()
        m.submodules.mem_core = mem_core = MemoryCore("host_to_fpga", 32, 1024)
        mem_core.base_addr = 0

        m.d.comb += bridge.bus_i.eq(mem_core.bus_o)
        m.d.comb += mem_core.bus_i.eq(bridge.bus_o)

        m.d.comb += [
            bridge.data_i.eq(self.data_i),
            bridge.valid_i.eq(self.valid_i),
            bridge.last_i.eq(self.last_i),
            self.ready_o.eq(bridge.ready_o),
            self.data_o.eq(bridge.data_o),
            self.valid_o.eq(bridge.valid_o),
            self.last_o.eq(bridge.last_o),
            bridge.ready_i.eq(self.ready_i),
        ]

        return m


bridge_plus_mem_core = EthernetBridgePlusMemoryCore()


@simulate(bridge_plus_mem_core)
async def test_ether_bridge_plus_mem_core(ctx):
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

    # await send_write_request(
    #     ctx,
    #     seq_num=0,
    #     addr=0x1234_5678,
    #     write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222, 0x3333_3333],
    # )
    # await send_write_request(ctx, seq_num=4, addr=0x1234_5678, write_data=[0x0000_0000, 0x1111_1111, 0x2222_2222])
    await send_read_request(ctx, bridge_plus_mem_core, seq_num=0, addr=0x1234_5678, read_length=1)
    # await send_bytes(ctx, [0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567])
    # await send_bytes(ctx, [0x0123_4567, 0x89AB_CDEF, 0x0123_4567, 0x89AB_CDEF])
    ctx.tick()

    for _ in range(20):
        await ctx.tick()
