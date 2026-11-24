from abc import ABC, abstractmethod

from amaranth import Elaboratable
from amaranth.lib import data


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

    @property
    @abstractmethod
    def top_level_ports(self):
        """
        Return the Amaranth signals that should be included as ports in the
        top-level Manta module.
        """

    @abstractmethod
    def to_config(self):
        """
        Return a dictionary containing the core's configuration (i.e., the
        content of the core's section of the `manta.yaml` file).
        """

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
                raise ValueError("Ran out of address space while allocating core.")

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
