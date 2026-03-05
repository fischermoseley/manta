import random

from cobs import cobs

from manta.uart.cobs_decode import COBSDecode
from manta.utils import *

cd = COBSDecode()


@simulate(cd)
async def test_cobs_decode_static(ctx):
    testcases = [
        # Test cases taken from Wikipedia:
        # https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing
        [0x00],
        [0x00, 0x00],
        [0x00, 0x11, 0x00],
        [0x11, 0x22, 0x00, 0x33],
        [0x11, 0x22, 0x33, 0x44],
        [0x11, 0x22, 0x33, 0x44, 0x00, 0x55, 0x66],
        [0x11, 0x00, 0x00, 0x00],
        [i for i in range(1, 255)],
        [0x00] + [i for i in range(1, 255)],
        [i for i in range(256)],
        [i for i in range(2, 256)] + [0x00],
        [i for i in range(3, 256)] + [0x00, 0x01],
        # # Selected edge and corner cases:
        [0x00] * 253,
        [0x00] * 254,
        [0x00] * 255,
        ([0x11] * 253) + [0],
        ([0x11] * 253) + [0] + ([0x11] * 5),
        ([0x11] * 254) + [0],
        ([0x11] * 255) + [0],
    ]

    for data in testcases:
        await decode_and_compare(ctx, data, tx_irritate=True, rx_irritate=True)


@simulate(cd)
async def test_cobs_decode_random(ctx):
    for _ in range(10):
        length = random.randint(1, 2000)

        population = [i for i in range(256)]
        no_preference = [1] * 256
        prefer_zeros = [10] + [1] * 255
        prefer_nonzeros = [1] + [10] * 255

        data_no_pref = random.choices(population, weights=no_preference, k=length)
        data_pref_zeros = random.choices(population, weights=prefer_zeros, k=length)
        data_pref_nonzeros = random.choices(population, weights=prefer_nonzeros, k=length)

        await decode_and_compare(ctx, data_no_pref, tx_irritate=True, rx_irritate=True)
        await decode_and_compare(ctx, data_pref_zeros, tx_irritate=True, rx_irritate=True)
        await decode_and_compare(ctx, data_pref_nonzeros, tx_irritate=True, rx_irritate=True)


async def decode(ctx, data, tx_irritate, rx_irritate):
    await ctx.tick().repeat(5)

    tx_done = False
    tx_index = 0
    rx_done = False
    rx_buf = []

    ctx.set(cd.source.ready, 1)
    await ctx.tick()

    while not (tx_done and rx_done):
        # Feed data to decoder
        tx_stall = random.randint(0, 1) if tx_irritate else False

        if tx_done or tx_stall:
            ctx.set(cd.sink.data, 0)
            ctx.set(cd.sink.valid, 0)

        else:
            ctx.set(cd.sink.valid, 1)
            ctx.set(cd.sink.data, data[tx_index])

            if ctx.get(cd.sink.valid) and ctx.get(cd.sink.ready):
                if tx_index == len(data) - 1:
                    tx_done = True

                else:
                    tx_index += 1

        # Randomly set source.ready if irritator is enabled
        ready = random.randint(0, 1) if rx_irritate else 1
        ctx.set(cd.source.ready, ready)

        # Pull output data from buffer
        if ctx.get(cd.source.valid) and ctx.get(cd.source.ready):
            rx_buf += [ctx.get(cd.source.data)]

            if ctx.get(cd.source.last):
                rx_done = True

        await ctx.tick()

    await ctx.tick().repeat(5)
    return rx_buf


async def decode_and_compare(ctx, data, tx_irritate, rx_irritate):
    encoded = cobs.encode(bytes(data)) + b"\0"

    # print([hex(a) for a in encoded])

    actual = await decode(ctx, encoded, tx_irritate, rx_irritate)
    matched = actual == data

    hex_print = lambda data: " ".join([f"{d:02x}" for d in data])

    if not matched:
        raise ValueError(
            "COBS decoder output does not match expected data!\n"
            f"   input: {hex_print(encoded)}\n"
            f"expected: {hex_print(data)}\n"
            f"  actual: {hex_print(actual)}\n"
        )
