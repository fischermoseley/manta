import random

from cobs import cobs

from manta.uart.cobs_encode import COBSEncode
from manta.utils import *

ce = COBSEncode()


@simulate(ce)
async def test_cobs_encode(ctx):
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()

    print("")

    ctx.set(ce.source.ready, 1)

    await encode_and_compare(ctx, [0x11, 0x22, 0x33, 0x44])
    # await encode_and_compare(ctx, [0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99])
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()

    await encode_and_compare(ctx, [0x11, 0x22, 0x00, 0x33])
    await ctx.tick()
    await ctx.tick()
    await ctx.tick()


@simulate(ce)
async def test_cobs_encode_random(ctx):
    ctx.set(ce.source.ready, 1)

    num_tests = random.randint(1, 5)
    for _ in range(num_tests):
        length = random.randint(1, 254)
        input_data = [random.randint(0, 255) for _ in range(length)]
        result = await encode_and_compare(ctx, input_data, quiet=True)
        await ctx.tick()
        await ctx.tick()
        await ctx.tick()

        if not result:
            await encode_and_compare(ctx, input_data, quiet=False)
            await ctx.tick()
            await ctx.tick()
            await ctx.tick()


async def encode(ctx, data):
    tx_done = False
    tx_index = 0
    rx_done = False
    rx_buf = []

    while not (tx_done and rx_done):
        # Feed data to encoder
        if not tx_done:
            ctx.set(ce.sink.valid, 1)
            ctx.set(ce.sink.data, data[tx_index])
            ctx.set(ce.sink.last, tx_index == len(data) - 1)

            if ctx.get(ce.sink.valid) and ctx.get(ce.sink.ready):
                if tx_index == len(data) - 1:
                    tx_done = True

                else:
                    tx_index += 1
        else:
            ctx.set(ce.sink.data, 0)
            ctx.set(ce.sink.valid, 0)
            ctx.set(ce.sink.last, 0)

        # Randomly set source.ready
        # ctx.set(ce.source.ready, random.randint(0, 1))
        ctx.set(ce.source.ready, 1)

        # Pull output data from buffer
        if ctx.get(ce.source.valid) and ctx.get(ce.source.ready):
            rx_buf += [ctx.get(ce.source.data)]

            if ctx.get(ce.source.last):
                rx_done = True

        await ctx.tick()

    await ctx.tick()
    await ctx.tick()
    await ctx.tick()

    return rx_buf


async def encode_and_compare(ctx, data, quiet=False):
    expected = cobs.encode(bytes(data)) + b"\0"
    actual = await encode(ctx, data)
    matched = bytes(actual) == expected

    if not quiet:
        print(f"   input: {[hex(d) for d in data]}")
        print(f"expected: {[hex(d) for d in expected]}")
        print(f"  actual: {[hex(d) for d in actual]}")
        print(f"  result: {'PASS' if matched else 'FAIL'}")
        print("")

    return matched
