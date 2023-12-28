from amaranth.sim import Simulator
from math import ceil
import os


def words_to_value(data):
    """
    Takes a list of integers, interprets them as 16-bit integers, and
    concatenates them together in little-endian order.
    """

    for d in data:
        if d > 0 and d > 2**16 - 1:
            raise ValueError("Unsigned integer too large.")

        if d < 0 and d < -(2**15 - 1):
            raise ValueError("Signed integer too large.")

    return int("".join([f"{i:016b}" for i in data[::-1]]), 2)


def value_to_words(data, n_words):
    """
    Takes a integer, interprets it as a set of 16-bit integers
    concatenated together, and splits it into a list of 16-bit numbers.
    """

    if not isinstance(data, int) or data < 0:
        raise ValueError("Behavior is only defined for nonnegative integers.")

    # convert to binary, split into 16-bit chunks, and then convert back to list of int
    binary = f"{data:0b}".zfill(n_words * 16)
    return [int(binary[i : i + 16], 2) for i in range(0, 16 * n_words, 16)][::-1]


def split_into_chunks(data, chunk_size):
    """
    Split a list into a list of lists, where each sublist has length `chunk_size`.
    If the list can't be evenly divided into chunks, then the last entry in the
    returned list will have length less than `chunk_size`.
    """

    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def simulate(top, testbench, vcd_path=None):
    """
    Run a behavior simulation using Amaranth's built-in simulator `pysim`. Takes
    the top-level module to simulate, the testbench process to run, and an optional
    path to export a VCD file to.
    """
    sim = Simulator(top)
    sim.add_clock(1e-6)  # 1 MHz
    sim.add_sync_process(testbench)

    if vcd_path is None:
        sim.run()

    else:
        with sim.write_vcd(vcd_path):
            sim.run()


def verify_register(module, addr, expected_data):
    """
    Read the contents of a register out over a module's bus connection, and verify
    that it contains the expected data.

    Unfortunately because Amaranth uses generator functions to define processes,
    this must be a generator function and thus cannot return a value - it must
    yield the next timestep. This means that the comparision with the expected
    value must occur inside this function and not somewhere else, it's not
    possible to return a value from here, and compare it in the calling function.
    """

    # place read transaction on the bus
    yield module.addr_i.eq(addr)
    yield module.data_i.eq(0)
    yield module.rw_i.eq(0)
    yield module.valid_i.eq(1)
    yield
    yield module.addr_i.eq(0)
    yield module.valid_i.eq(0)

    # wait for output to be valid
    while not (yield module.valid_o):
        yield

    # compare returned value with expected
    data = yield (module.data_o)
    if data != expected_data:
        raise ValueError(f"Read from {addr} yielded {data} instead of {expected_data}")


def write_register(module, addr, data):
    """
    Write to a register over a module's bus connection, placing the contents of `data`
    at `addr`.
    """

    yield module.addr_i.eq(addr)
    yield module.data_i.eq(data)
    yield module.rw_i.eq(1)
    yield module.valid_i.eq(1)
    yield
    yield module.valid_i.eq(0)
    yield


def xilinx_tools_installed():
    """
    Return whether Vivado is installed, by checking if the VIVADO environment variable is set.

    This variable should point to the binary itself, not just the folder it's located in
    (ie, /tools/Xilinx/Vivado/2023.1/bin/vivado, not /tools/Xilinx/Vivado/2023.1/bin)
    """
    return "VIVADO" in os.environ


def ice40_tools_installed():
    """
    Return whether the ice40 tools are installed, by checking if the YOSYS, NEXTPNR_ICE40,
    ICEPACK, and ICEPROG environment variables are defined.

    # These variables should point to the binaries themselves, not just the folder it's located in
    # (ie, /tools/oss-cad-suite/bin/yosys, not /tools/oss-cad-suite/bin/)
    """
    tools = ["YOSYS", "NEXTPNR_ICE40", "ICEPACK", "ICEPROG"]
    return all(tool in os.environ for tool in tools)
