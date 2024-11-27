import os
from abc import ABC, abstractmethod
from pathlib import Path
from random import sample

from amaranth import Elaboratable
from amaranth.lib import data
from amaranth.sim import Simulator


class MantaCore(ABC, Elaboratable):
    # These attributes are meant to be settable and gettable, but max_addr and
    # top_level_ports are intended to be only gettable. Do not implement
    # setters for them in subclasses.

    base_addr = None
    interface = None

    @property
    @abstractmethod
    def max_addr(self):
        """
        Return the maximum addresses in memory used by the core. The address
        space used by the core extends from `base_addr` to the number returned
        by this function (including the endpoints).
        """
        pass

    @property
    @abstractmethod
    def top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """
        pass

    @abstractmethod
    def to_config(self):
        """
        Return a dictionary containing the core's configuration (i.e., the
        content of the core's section of the `manta.yaml` file).
        """
        pass

    @abstractmethod
    def elaborate(self, platform):
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config):
        """
        Return an instance of the core, given the section of the Manta
        configuration file (as a Python dictionary) that contains the core's
        specification.
        """
        pass


class CoreContainer:
    def __init__(self, manta):
        self._manta = manta
        self._cores = {}
        self._base_addr = 0
        self._last_used_addr = 0

    def __getattr__(self, name):
        if name in self._cores:
            return self._cores[name]
        raise AttributeError(f"No such core: {name}")

    def __setattr__(self, name, value):
        if name in {"_manta", "_cores", "_base_addr", "_last_used_addr"}:
            super().__setattr__(name, value)
        else:
            self._cores[name] = value
            value.interface = self._manta.interface
            value.base_addr = self._last_used_addr

            if value.max_addr > (2**16) - 1:
                raise ValueError(f"Ran out of address space while allocating core.")

            self._last_used_addr = value.max_addr + 1


class InternalBus(data.StructLayout):
    """
    Describes the layout of Manta's internal bus, such that signals of
    the appropriate dimension can be instantiated with Signal(InternalBus()).
    """

    def __init__(self):
        super().__init__(
            {
                "addr": 16,
                "data": 16,
                "rw": 1,
                "valid": 1,
                "last": 1,
            }
        )


def warn(message):
    """
    Prints a warning to the user's terminal. Originally the warn() method
    from the builtin warnings module was used for this, but I don't think the
    way it outputs on the command line is the most helpful for the users.
    (ie, Users don't care about the stacktrace or the filename/line number.)
    """
    print("Warning: " + message)


def words_to_value(data):
    """
    Takes a list of integers, interprets them as 16-bit integers, and
    concatenates them together in little-endian order.
    """

    [check_value_fits_in_bits(d, 16) for d in data]

    return int("".join([f"{i:016b}" for i in data[::-1]]), 2)


def value_to_words(data, n_words):
    """
    Takes a integer, interprets it as a set of 16-bit integers
    concatenated together, and splits it into a list of 16-bit numbers.
    """

    if not isinstance(data, int) or data < 0:
        raise ValueError("Behavior is only defined for nonnegative integers.")

    # Convert to binary, split into 16-bit chunks, and then convert back to list of int
    binary = f"{data:0b}".zfill(n_words * 16)
    return [int(binary[i : i + 16], 2) for i in range(0, 16 * n_words, 16)][::-1]


def check_value_fits_in_bits(value, n_bits):
    """
    Raises an exception if the provided value isn't an integer that cannot
    be expressed with the provided number of bits.
    """

    if not isinstance(value, int):
        raise TypeError("Value must be an integer.")

    if value > 0 and value > 2**n_bits - 1:
        raise ValueError("Unsigned integer too large.")

    if value < 0 and value < -(2 ** (n_bits - 1)):
        raise ValueError("Signed integer too large.")


def split_into_chunks(data, chunk_size):
    """
    Split a list into a list of lists, where each sublist has length `chunk_size`.
    If the list can't be evenly divided into chunks, then the last entry in the
    returned list will have length less than `chunk_size`.
    """

    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


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

    if all([which(b) for b in binaries]):
        return True

    return False
