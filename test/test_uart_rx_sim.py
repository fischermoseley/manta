from manta.uart import UARTReceiver
from manta.utils import *

uart_rx = UARTReceiver(clocks_per_baud=10)


async def verify_receive(ctx, data):
    # 8N1 serial, LSB sent first
    data_bits = "0" + f"{data:08b}"[::-1] + "1"
    data_bits = [int(bit) for bit in data_bits]

    valid_asserted_before = False

    for i in range(10 * uart_rx._clocks_per_baud):
        bit_index = i // uart_rx._clocks_per_baud

        # Every cycle, run checks on uart_rx:
        if ctx.get(uart_rx.valid_o):
            if ctx.get(uart_rx.data_o) != data:
                a = ctx.get(uart_rx.data_o)
                print(data_bits)
                raise ValueError(
                    f"Incorrect byte presented - gave {hex(a)} instead of {hex(data)}!"
                )

            if bit_index != 9:
                print(bit_index)
                raise ValueError("Byte presented before it is complete!")

            if not valid_asserted_before:
                valid_asserted_before = True

            else:
                raise ValueError("Valid asserted more than once!")

        ctx.set(uart_rx.rx, data_bits[bit_index])
        await ctx.tick()

    if not valid_asserted_before:
        raise ValueError("Failed to assert valid!")


@simulate(uart_rx)
async def test_all_possible_bytes(ctx):
    ctx.set(uart_rx.rx, 1)
    await ctx.tick()

    for i in range(0xFF):
        await verify_receive(ctx, i)


@simulate(uart_rx)
async def test_bytes_random_sample(ctx):
    ctx.set(uart_rx.rx, 1)
    await ctx.tick()

    for i in jumble(range(0xFF)):
        await verify_receive(ctx, i)
