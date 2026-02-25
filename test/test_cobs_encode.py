import random

from cobs import cobs

from manta.uart.cobs_encode import COBSEncode
from manta.utils import *

ce = COBSEncode()


@simulate(ce)
async def test_cobs_encode_static(ctx):
    testcases = [
        # Test cases taken from Wikipedia:
        # https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
        [0x00],
        [0x00, 0x00],
        [0x00, 0x11, 0x00],
        [0x11, 0x22, 0x00, 0x33],
        [0x11, 0x22, 0x33, 0x44],
        [0x11, 0x00, 0x00, 0x00],
        [i for i in range(1, 255)],
        [0x00] + [i for i in range(1, 255)],
        [i for i in range(256)],
        [i for i in range(2, 256)] + [0x00],
        [i for i in range(3, 256)] + [0x00, 0x01],
        # Selected edge and corner cases:
        [0x00] * 253,
        [0x00] * 254,
        [0x00] * 255,
        ([0x11] * 253) + [0],
        ([0x11] * 253) + [0] + ([0x11] * 5),
        ([0x11] * 254) + [0],
        ([0x11] * 255) + [0],
    ]

    for data in testcases:
        await encode_and_compare(ctx, data, tx_irritate=True, rx_irritate=True)


@simulate(ce)
async def test_cobs_encode_random(ctx):
    num_tests = random.randint(1, 5)
    for _ in range(num_tests):
        length = random.randint(1, 2000)
        data = [random.randint(0, 255) for _ in range(length)]
        await encode_and_compare(ctx, data, tx_irritate=True, rx_irritate=True)


async def encode(ctx, data, tx_irritate, rx_irritate):
    await ctx.tick().repeat(5)

    tx_done = False
    tx_index = 0
    rx_done = False
    rx_buf = []

    while not (tx_done and rx_done):
        # Feed data to encoder
        tx_stall = random.randint(0, 1) if tx_irritate else False

        if not tx_done and not tx_stall:
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

        # Randomly set source.ready if irritator is enabled
        ready = random.randint(0, 1) if rx_irritate else 1
        ctx.set(ce.source.ready, ready)

        # Pull output data from buffer
        if ctx.get(ce.source.valid) and ctx.get(ce.source.ready):
            rx_buf += [ctx.get(ce.source.data)]

            if ctx.get(ce.source.last):
                rx_done = True

        await ctx.tick()

    await ctx.tick().repeat(5)
    return rx_buf


async def encode_and_compare(ctx, data, tx_irritate, rx_irritate):
    expected = cobs.encode(bytes(data)) + b"\0"
    actual = await encode(ctx, data, tx_irritate, rx_irritate)
    matched = bytes(actual) == expected

    hex_print = lambda data: " ".join([f"{d:02x}" for d in data])

    if not matched:
        raise ValueError(
            "COBS encoder output does not match expected data!\n"
            f"   input: {hex_print(data)}\n"
            f"expected: {hex_print(expected)}\n"
            f"  actual: {hex_print(actual)}\n"
        )
