import os
from pathlib import Path
from random import sample

from amaranth.sim import Simulator


def xilinx_tools_installed():
    """
    Return whether Vivado is installed, by checking if the VIVADO environment variable is set,
    or if the binary exists on PATH.

    This variable should point to the binary itself, not just the folder it's located in
    (ie, /tools/Xilinx/Vivado/2023.1/bin/vivado, not /tools/Xilinx/Vivado/2023.1/bin)
    """
    from shutil import which

    return ("VIVADO" in os.environ) or (which("vivado") is not None)


def ice40_tools_installed():
    """
    Return whether the ice40 tools are installed, by checking if the YOSYS, NEXTPNR_ICE40,
    ICEPACK, and ICEPROG environment variables are defined, or if the binaries exist on PATH.

    # These variables should point to the binaries themselves, not just the folder it's located in
    # (ie, /tools/oss-cad-suite/bin/yosys, not /tools/oss-cad-suite/bin/)
    """

    # Check environment variables
    env_vars = ["YOSYS", "NEXTPNR_ICE40", "ICEPACK", "ICEPROG"]
    if all(var in os.environ for var in env_vars):
        return True

    # Check PATH
    binaries = ["yosys", "nextpnr-ice40", "icepack", "iceprog"]
    from shutil import which

    return all(which(b) for b in binaries)


def jumble(iterable):
    """
    Returns the provided iterable, but with every element moved to a random
    index. Very similar to random.shuffle, but returns an iterable, instead
    of modifying one in-place.
    """
    return sample(iterable, len(iterable))


async def verify_register(module, ctx, addr, expected_data):
    """
    Read the contents of a register out over a module's bus connection, and
    verify that it contains the expected data.

    Unfortunately because Amaranth uses generator functions to define processes,
    this must be a generator function and thus cannot return a value - it must
    yield the next timestep. This means that the comparison with the expected
    value must occur inside this function and not somewhere else, it's not
    possible to return a value from here, and compare it in the calling
    function.
    """

    # Place read transaction on the bus
    ctx.set(module.bus_i.addr, addr)
    ctx.set(module.bus_i.data, 0)
    ctx.set(module.bus_i.valid, True)
    ctx.set(module.bus_i.rw, 0)
    await ctx.tick()
    ctx.set(module.bus_i.addr, 0)
    ctx.set(module.bus_i.valid, 0)

    # Wait for output to be valid
    while not ctx.get(module.bus_o.valid):
        await ctx.tick()

    # Compare returned value with expected
    data = ctx.get(module.bus_o.data)
    if data != expected_data:
        raise ValueError(f"Read from {addr} yielded {data} instead of {expected_data}")


async def write_register(module, ctx, addr, data):
    """
    Write to a register over a module's bus connection, placing the contents of `data`
    at `addr`.
    """

    ctx.set(module.bus_i.addr, addr)
    ctx.set(module.bus_i.data, data)
    ctx.set(module.bus_i.rw, 1)
    ctx.set(module.bus_i.valid, True)
    await ctx.tick()
    ctx.set(module.bus_i.addr, 0)
    ctx.set(module.bus_i.data, 0)
    ctx.set(module.bus_i.rw, 0)
    ctx.set(module.bus_i.valid, False)
    await ctx.tick()


def make_build_dir_if_it_does_not_exist_already():
    """
    Make build/ if it doesn't exist already.
    """

    Path("build").mkdir(parents=True, exist_ok=True)


def simulate(top):
    """
    A decorator for running behavioral simulation using Amaranth's built-in
    simulator. Requires the top-level module in the simulation as an argument,
    and automatically names VCD file containing the waveform dump in build/
    with the name of the function being decorated.
    """

    def decorator(testbench):
        make_build_dir_if_it_does_not_exist_already()

        def wrapper(*args, **kwargs):
            sim = Simulator(top)
            sim.add_clock(1e-6)  # 1 MHz
            sim.add_testbench(testbench)

            vcd_path = "build/" + testbench.__name__ + ".vcd"

            with sim.write_vcd(vcd_path):
                sim.run()

        return wrapper

    return decorator
