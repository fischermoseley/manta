from manta.uart import UARTTransmitter
from manta.utils import *

uart_tx = UARTTransmitter(clocks_per_baud=10)


async def verify_bit_sequence(ctx, byte):
    """
    Request a byte to be transmitted, and verify that the sequence of bits is correct.
    """

    # Request byte to be transmitted
    ctx.set(uart_tx.data_i, byte)
    ctx.set(uart_tx.start_i, 1)
    await ctx.tick()

    ctx.set(uart_tx.data_i, 0)
    ctx.set(uart_tx.start_i, 0)

    # Check that data bit is correct on every clock baud period

    # 8N1 serial, LSB sent first
    data_bits = "0" + f"{byte:08b}"[::-1] + "1"
    data_bits = [int(bit) for bit in data_bits]

    for i in range(10 * uart_tx._clocks_per_baud):
        bit_index = i // uart_tx._clocks_per_baud

        if ctx.get(uart_tx.tx) != data_bits[bit_index]:
            raise ValueError("Wrong bit in sequence!")

        if ctx.get(uart_tx.done_o) and (bit_index != 9):
            raise ValueError("Done asserted too early!")

        await ctx.tick()

    if not ctx.get(uart_tx.done_o):
        raise ValueError("Done not asserted at end of transmission!")


@simulate(uart_tx)
async def test_all_possible_bytes(ctx):
    for i in range(0xFF):
        await verify_bit_sequence(ctx, i)


@simulate(uart_tx)
async def test_bytes_random_sample(ctx):
    for i in jumble(range(0xFF)):
        await verify_bit_sequence(ctx, i)
