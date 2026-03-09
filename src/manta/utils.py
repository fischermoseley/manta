import os
from abc import ABC, abstractmethod
from pathlib import Path
from random import sample

from amaranth import Cat, Const, Elaboratable, Signal, unsigned
from amaranth.lib import data, wiring
from amaranth.lib.data import Struct
from amaranth.lib.enum import IntEnum
from amaranth.lib.wiring import In, Out
from amaranth.sim import Simulator


class MantaCore(ABC, wiring.Component):
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


InternalBusLayout = data.StructLayout(
    {
        "addr": 32,
        "data": 32,
        "rw": 1,
        "valid": 1,
    }
)

InternalBusSignature = wiring.Signature({"p": Out(InternalBusLayout)})


class StreamSignature(wiring.Signature):
    def __init__(self, data_shape, has_last=True, has_ready=True):
        sig = {
            "data": Out(data_shape),
            "valid": Out(1),
        }

        if has_last:
            sig["last"] = Out(1)

        if has_ready:
            sig["ready"] = In(1)

        super().__init__(sig)

    def __eq__(self, other):
        return self.members == other.members


class MessageTypes(IntEnum, shape=unsigned(3)):
    READ_REQUEST = 0
    WRITE_REQUEST = 1
    READ_RESPONSE = 2
    WRITE_RESPONSE = 3
    NACK = 4


class EthernetMessageHeader(Struct):
    msg_type: MessageTypes
    seq_num: 13
    length: 7 = 0
    zero_padding: 9 = 0

    # TODO: determine if observed 63 word limit is a bug or just a limitation of LiteEth
    MAX_READ_LENGTH = 63
    MAX_WRITE_LENGTH = 63

    @classmethod
    def from_params(cls, msg_type, seq_num, length=0):
        return cls.const(init={"msg_type": msg_type, "seq_num": seq_num, "length": length})

    @classmethod
    def concat_signals(cls, msg_type: MessageTypes, seq_num: Signal, length: Signal = None):
        # Make sure each signal is the right width!
        widths = cls.from_bits(0).shape().members

        if Const(msg_type).shape().width != MessageTypes.as_shape().width:
            raise TypeError

        if seq_num.shape().width != widths["seq_num"]:
            raise TypeError

        zp_width = widths["zero_padding"]
        len_width = widths["length"]

        if length is None:
            return Cat(msg_type, seq_num, Const(0, len_width), Const(0, zp_width))

        else:
            if length.shape().width != len_width:
                raise TypeError

            return Cat(msg_type, seq_num, length, Const(0, zp_width))


def warn(message):
    """
    Prints a warning to the user's terminal. Originally the warn() method
    from the builtin warnings module was used for this, but I don't think the
    way it outputs on the command line is the most helpful for the users.
    (ie, Users don't care about the stacktrace or the filename/line number.)
    """
    print("Warning: " + message)


def parse_sequences(numbers):
    """
    Takes a list of integers and identifies runs of sequential numbers
    (where each number is exactly 1 more than the previous). Returns
    a list of tuples, where each tuple contains the starting number
    and the length of that sequence.
    """

    if not numbers:
        return []

    sequences = []
    start = numbers[0]
    length = 1

    for i in range(1, len(numbers)):
        if numbers[i] == numbers[i - 1] + 1:
            length += 1
        else:
            sequences.append((start, length))
            start = numbers[i]
            length = 1

    sequences.append((start, length))
    return sequences


def words_to_value(data, width=32):
    """
    Takes a list of integers, interprets them as n-bit integers, and
    concatenates them together in little-endian order.
    """

    for d in data:
        check_value_fits_in_bits(d, width)

    result = 0
    for word in reversed(data):
        result = (result << width) | word
    return result


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


def ints_from_bytestring(bytes, byteorder="little"):
    """
    Takes a list of ints, interprets them as 32-bit integers, and returns a
    bytestring of the constituent bytes joined together.
    """
    return [int.from_bytes(chunk, byteorder) for chunk in split_into_chunks(bytes, 4)]


def bytestring_from_ints(ints, byteorder="little"):
    """
    Takes a list of ints, interprets them as 32-bit integers, and returns a
    bytestring of the constituent bytes joined together.
    """
    return b"".join(i.to_bytes(4, byteorder) for i in ints)


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
