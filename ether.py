# Test with 32-bit data/valid/ready/last interface for input, and one for output

from amaranth import *
from amaranth.lib.enum import IntEnum

from manta.utils import *


class MessageTypes(IntEnum, shape=unsigned(3)):
    READ_REQUEST = 0
    WRITE_REQUEST = 1
    READ_RESPONSE = 2
    WRITE_RESPONSE = 3
    NACK = 4


class EthernetBridge(Elaboratable):
    def __init__(self):
        self.data_i = Signal(32)
        self.valid_i = Signal()
        self.last_i = Signal()
        self.ready_o = Signal()

        self.data_o = Signal(32)
        self.valid_o = Signal()
        self.last_o = Signal()
        self.ready_i = Signal()

        self.bus_o = Signal(InternalBus())
        self.bus_i = Signal(InternalBus())

    def elaborate(self, platform):
        m = Module()

        seq_num_expected = Signal(13)
        read_len = Signal(7)

        with m.FSM(init="IDLE"):
            with m.State("IDLE"):
                m.d.sync += self.ready_o.eq(1)

                with m.If(self.valid_i):
                    # First 32 bits was presented, which contains message type (first 3 bits)
                    # as well as sequence number (next 13 bits). The remaining 16 bits are unused.

                    # Send NACK if message type or sequence number is incorrect
                    with m.If(
                        (self.data_i[:3] > max(MessageTypes))
                        | (self.data_i[3:16] != seq_num_expected)
                    ):
                        # Wait to NACK if this isn't the last beat in message
                        with m.If(~self.last_i):
                            m.next = "NACK_WAIT_FOR_LAST"

                        # Otherwise, NACK immediately
                        with m.Else():
                            m.d.sync += self.data_o.eq(
                                Cat(MessageTypes.NACK, seq_num_expected)
                            )
                            m.d.sync += self.valid_o.eq(1)
                            m.d.sync += self.last_o.eq(1)
                            m.d.sync += self.ready_o.eq(0)
                            m.next = "NACK_WAIT_FOR_READY"

                    with m.Elif(self.data_i[:3] == MessageTypes.READ_REQUEST):
                        m.d.sync += seq_num_expected.eq(seq_num_expected + 1)
                        m.d.sync += read_len.eq(self.data_i[16:23] - 1)

                        m.d.sync += self.data_o.eq(
                            Cat(MessageTypes.READ_RESPONSE, seq_num_expected + 1)
                        )
                        m.next = "READ_WAIT_FOR_ADDR"

                    with m.Elif(self.data_i[:3] == MessageTypes.WRITE_REQUEST):
                        m.d.sync += seq_num_expected.eq(seq_num_expected + 1)
                        m.next = "WRITE_WAIT_FOR_ADDR"

            with m.State("READ_WAIT_FOR_ADDR"):
                with m.If(self.valid_i):
                    # we have the length and the address to read from, let's go!
                    m.d.sync += self.bus_o.addr.eq(self.data_i)
                    m.d.sync += self.bus_o.data.eq(0)
                    m.d.sync += self.bus_o.rw.eq(0)
                    m.d.sync += self.bus_o.valid.eq(1)

                    with m.If(read_len == 0):
                        # we've sent the last read request in this batch to the bus
                        m.d.sync += self.bus_o.last.eq(1)
                        m.d.sync += read_len.eq(0)

                    m.next = "READ"

            with m.State("READ"):
                m.d.sync += self.ready_o.eq(0)

                # Clock out read requests to the bus
                with m.If(read_len > 0):
                    m.d.sync += self.bus_o.addr.eq(self.bus_o.addr + 1)
                    m.d.sync += read_len.eq(read_len - 1)

                    with m.If(read_len == 1):
                        m.d.sync += self.bus_o.last.eq(1)

                with m.Else():
                    m.d.sync += self.bus_o.eq(
                        0
                    )  # TODO: it's probably overzealous to set the whole bus to zero, but it makes debugging easy so we're doing it xD

                # Clock out any read data from the bus
                with m.If(self.bus_i.valid):
                    m.d.sync += self.data_o.eq(self.bus_i.data)

                    with m.If(self.bus_i.last):
                        m.d.sync += self.last_o.eq(1)
                        m.next = "IDLE"  # TODO: could save a cycle by checking valid_i to see if there's more work to do

            with m.State("WRITE_WAIT_FOR_ADDR"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_i.addr.eq(self.data_i)
                    m.next = "WRITE_FIRST"

            # Don't want to increment address on the first write,
            # and I'm lazy so I'm making a new state to keep track of that
            with m.State("WRITE_FIRST"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_o.data.eq(self.data_i)
                    m.d.sync += self.bus_o.rw.eq(1)
                    m.d.sync += self.bus_o.valid.eq(1)
                    m.d.sync += self.bus_o.last.eq(self.last_i)

                    with m.If(self.last_i):
                        m.next = "IDLE"  # TODO: could save a cycle by checking valid_i to see if there's more work to do

                    with m.Else():
                        m.next = "WRITE"

            with m.State("WRITE"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_o.addr.eq(self.bus_i.addr + 1)
                    m.d.sync += self.bus_o.data.eq(self.data_i)
                    m.d.sync += self.bus_o.rw.eq(1)
                    m.d.sync += self.bus_o.valid.eq(1)
                    m.d.sync += self.bus_o.last.eq(self.last_i)

                with m.Else():
                    m.d.sync += self.bus_o.eq(0)

                with m.If(self.bus_o.last):
                    m.d.sync += self.bus_o.valid.eq(0)
                    m.d.sync += self.bus_o.addr.eq(0)
                    m.d.sync += self.bus_o.data.eq(0)
                    m.d.sync += self.bus_o.last.eq(0)
                    m.d.sync += self.bus_o.rw.eq(0)
                    m.next = "IDLE"  # TODO: could save a cycle by checking valid_i to see if there's more work to do

                with m.Else():
                    m.next = "WRITE"

            with m.State("NACK_WAIT_FOR_LAST"):
                with m.If(self.last_i):
                    m.d.sync += self.data_o.eq(Cat(MessageTypes.NACK, seq_num_expected))
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.last_o.eq(1)
                    m.d.sync += self.ready_o.eq(0)
                    m.next = "NACK_WAIT_FOR_READY"

            with m.State("NACK_WAIT_FOR_READY"):
                with m.If(self.ready_i):
                    m.d.sync += self.valid_o.eq(0)

                    # TODO: remove these next two lines, they're not necessary
                    # although they are nice for debug...
                    m.d.sync += self.data_o.eq(0)
                    m.d.sync += self.last_o.eq(0)
                    m.d.sync += self.ready_o.eq(1)

                    m.next = "IDLE"

        return m


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
