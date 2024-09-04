from random import getrandbits

from amaranth import *

from manta import *
from manta.utils import *

probe0 = Signal(1)
probe1 = Signal(2)
probe2 = Signal(8)
probe3 = Signal(20)
inputs = [probe0, probe1, probe2, probe3]

probe4 = Signal(1, init=1)
probe5 = Signal(2, init=2)
probe6 = Signal(8)
probe7 = Signal(20, init=65538)
outputs = [probe4, probe5, probe6, probe7]

io_core = IOCore(inputs=inputs, outputs=outputs)
io_core.base_addr = 0
_ = io_core.max_addr


async def pulse_strobe_register(ctx):
    strobe_addr = io_core._memory_map["strobe"]["addrs"][0]
    await write_register(io_core, ctx, strobe_addr, 0)
    await write_register(io_core, ctx, strobe_addr, 1)
    await write_register(io_core, ctx, strobe_addr, 0)


@simulate(io_core)
async def test_input_probe_buffer_initial_value(ctx):
    # Verify all input probe buffers initialize to zero
    for i in inputs:
        addrs = io_core._memory_map[i.name]["addrs"]

        for addr in addrs:
            await verify_register(io_core, ctx, addr, 0)


@simulate(io_core)
async def test_output_probe_buffer_initial_value(ctx):
    # Verify all output probe buffers initialize to the values in the config
    for o in outputs:
        addrs = io_core._memory_map[o.name]["addrs"]
        datas = value_to_words(o.init, len(addrs))

        for addr, data in zip(addrs, datas):
            await verify_register(io_core, ctx, addr, data)


@simulate(io_core)
async def test_output_probes_are_writeable(ctx):
    for o in outputs:
        addrs = io_core._memory_map[o.name]["addrs"]
        test_value = getrandbits(len(o))
        datas = value_to_words(test_value, len(addrs))

        # write value to registers
        for addr, data in zip(addrs, datas):
            await write_register(io_core, ctx, addr, data)

        # read value back from registers
        for addr, data in zip(addrs, datas):
            await verify_register(io_core, ctx, addr, data)


@simulate(io_core)
async def test_output_probes_update(ctx):
    for o in outputs:
        addrs = io_core._memory_map[o.name]["addrs"]
        test_value = getrandbits(len(o))
        datas = value_to_words(test_value, len(addrs))

        # write value to registers
        for addr, data in zip(addrs, datas):
            await write_register(io_core, ctx, addr, data)

        # pulse strobe register
        await pulse_strobe_register(ctx)

        # check that outputs took updated value
        value = ctx.get(o)

        if value != test_value:
            raise ValueError(
                f"Output probe {o.name} took value {value} instead of {test_value} after pulsing strobe."
            )

        else:
            print(f"Output probe {o.name} took value {value} after pulsing strobe.")


@simulate(io_core)
async def test_input_probes_update(ctx):
    for i in inputs:
        # set input probe value
        test_value = getrandbits(len(i))
        ctx.set(i, test_value)

        # pulse strobe register
        await pulse_strobe_register(ctx)

        # check that values are as expected once read back
        addrs = io_core._memory_map[i.name]["addrs"]
        datas = value_to_words(test_value, len(addrs))

        for addr, data in zip(addrs, datas):
            await verify_register(io_core, ctx, addr, data)
