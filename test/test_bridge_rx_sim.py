from manta.uart import ReceiveBridge
from manta.utils import *

bridge_rx = ReceiveBridge()


async def verify_read_decoding(ctx, bytes, addr):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge places
    a read request with the appropriate address on the internal bus.
    """

    valid_asserted = False
    ctx.set(bridge_rx.valid_i, True)

    for i, byte in enumerate(bytes):
        ctx.set(bridge_rx.data_i, byte)

        if ctx.get(bridge_rx.valid_o) and (i > 0):
            valid_asserted = True
            if ctx.get(bridge_rx.addr_o) != addr:
                raise ValueError("wrong addr!")

            if ctx.get(bridge_rx.rw_o) != 0:
                raise ValueError("wrong rw!")

            if ctx.get(bridge_rx.data_o) != 0:
                raise ValueError("wrong data!")

        await ctx.tick()

    ctx.set(bridge_rx.valid_i, False)
    ctx.set(bridge_rx.data_i, 0)

    if not valid_asserted and not ctx.get(bridge_rx.valid_o):
        raise ValueError("Bridge failed to output valid message.")


async def verify_write_decoding(ctx, bytes, addr, data):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge places
    a write request with the appropriate address and data on the internal bus.
    """
    valid_asserted = False
    ctx.set(bridge_rx.valid_i, True)

    for i, byte in enumerate(bytes):
        ctx.set(bridge_rx.data_i, byte)

        if ctx.get(bridge_rx.valid_o) and (i > 0):
            valid_asserted = True
            if ctx.get(bridge_rx.addr_o) != addr:
                raise ValueError("wrong addr!")

            if ctx.get(bridge_rx.rw_o) != 1:
                raise ValueError("wrong rw!")

            if ctx.get(bridge_rx.data_o) != data:
                raise ValueError("wrong data!")

        await ctx.tick()

    ctx.set(bridge_rx.valid_i, False)
    ctx.set(bridge_rx.data_i, 0)

    if not valid_asserted and not ctx.get(bridge_rx.valid_o):
        raise ValueError("Bridge failed to output valid message.")


async def verify_bad_bytes(ctx, bytes):
    """
    Send a series of bytes to the receive bridge, and verify that the bridge does not
    place any transaction on the internal bus.
    """
    ctx.set(bridge_rx.valid_i, True)

    for byte in bytes:
        ctx.set(bridge_rx.data_i, byte)

        if ctx.get(bridge_rx.valid_o):
            raise ValueError("Bridge decoded invalid message.")

        await ctx.tick()

    ctx.set(bridge_rx.valid_i, 0)


@simulate(bridge_rx)
async def test_function(ctx):
    await verify_read_decoding(ctx, b"R0000\r\n", 0x0000)
    await verify_read_decoding(ctx, b"R1234\r\n", 0x1234)
    await verify_read_decoding(ctx, b"RBABE\r\n", 0xBABE)
    await verify_read_decoding(ctx, b"R5678\n", 0x5678)
    await verify_read_decoding(ctx, b"R9ABC\r", 0x9ABC)


@simulate(bridge_rx)
async def test_write_decode(ctx):
    await verify_write_decoding(ctx, b"W12345678\r\n", 0x1234, 0x5678)
    await verify_write_decoding(ctx, b"WDEADBEEF\r\n", 0xDEAD, 0xBEEF)
    await verify_write_decoding(ctx, b"WDEADBEEF\r", 0xDEAD, 0xBEEF)
    await verify_write_decoding(ctx, b"WB0BACAFE\n", 0xB0BA, 0xCAFE)


@simulate(bridge_rx)
async def test_no_decode(ctx):
    await verify_bad_bytes(ctx, b"RABC\r\n")
    await verify_bad_bytes(ctx, b"R12345\r\n")
    await verify_bad_bytes(ctx, b"M\r\n")
    await verify_bad_bytes(ctx, b"W123456789101112131415161718191201222\r\n")
    await verify_bad_bytes(ctx, b"RABCG\r\n")
    await verify_bad_bytes(ctx, b"WABC[]()##*@\r\n")
    await verify_bad_bytes(ctx, b"R\r\n")
