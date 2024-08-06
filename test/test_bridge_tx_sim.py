from random import sample

from manta.uart import TransmitBridge
from manta.utils import *

bridge_tx = TransmitBridge()


async def verify_encoding(ctx, data, bytes):
    """
    Place a read response on the internal bus, and verify that the sequence of bytes
    sent from TransmitBridge matches the provided bytestring `bytes`.

    This function also models an ideal UARTTransmitter module, which begins transmitting
    bytes when `start` is asserted, and reports when it is done by asserting `done`.
    """

    # Place a read response on the internal bus
    ctx.set(bridge_tx.data_i, data)
    ctx.set(bridge_tx.valid_i, True)
    ctx.set(bridge_tx.rw_i, 0)
    ctx.set(bridge_tx.done_i, True)

    await ctx.tick()

    ctx.set(bridge_tx.data_i, 0)
    ctx.set(bridge_tx.valid_i, False)
    ctx.set(bridge_tx.rw_i, 0)

    # Model the UARTTransmitter
    sent_bytes = b""
    iters = 0

    while len(sent_bytes) < len(bytes):
        # If start_o is asserted, set done_i to zero, then delay, then set it back to one
        if ctx.get(bridge_tx.start_o):
            sent_bytes += ctx.get(bridge_tx.data_o).to_bytes(1, "big")
            ctx.set(bridge_tx.done_i, 0)

            for _ in range(10):
                await ctx.tick()

            ctx.set(bridge_tx.done_i, 1)
            await ctx.tick()

        # Time out if not enough bytes after trying to get bytes 15 times
        iters += 1
        if iters > 15:
            raise ValueError("Timed out waiting for bytes.")

    # Verify bytes sent from ReceiveBridge match expected_bytes
    if sent_bytes != bytes:
        raise ValueError(f"Received {sent_bytes} instead of {bytes}.")


@simulate(bridge_tx)
async def test_some_random_values(ctx):
    for i in sample(range(0xFFFF), k=5000):
        expected = f"D{i:04X}\r\n".encode("ascii")
        await verify_encoding(ctx, i, expected)
