from manta.memory_core import MemoryCore
from manta.utils import *
from random import randint, choice
from math import ceil


class MemoryCoreTests:
    def __init__(self, mem_core):
        self.mem_core = mem_core
        self.base_addr = mem_core._base_addr
        self.max_addr = mem_core.max_addr
        self.width = self.mem_core._width
        self.depth = self.mem_core._depth
        self.n_full = self.width // 16
        self.n_mems = ceil(self.width / 16)

        self.bus_addrs = list(
            range(self.base_addr, self.max_addr)
        )  # include the endpoint!
        self.user_addrs = list(range(self.mem_core._depth))
        self.model = {}

    def bus_addrs_all_zero(self):
        for addr in self.bus_addrs:
            yield from self.verify_bus_side(addr, 0)

    def user_addrs_all_zero(self):
        for addr in self.user_addrs:
            yield from self.verify_user_side(addr, 0)

    def one_bus_write_then_one_bus_read(self):
        for addr in self.bus_addrs:
            data_width = self.get_data_width(addr)
            data = randint(0, (2**data_width) - 1)

            yield from self.write_bus_side(addr, data)
            yield from self.verify_bus_side(addr, data)

    def multi_bus_writes_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for addr in jumble(self.bus_addrs):
            data_width = self.get_data_width(addr)
            data = randint(0, (2**data_width) - 1)

            self.model[addr] = data
            yield from self.write_bus_side(addr, data)

        for addr in jumble(self.bus_addrs):
            yield from self.verify_bus_side(addr, self.model[addr])

    def rand_bus_reads_writes(self):
        # random reads and writes in random orders
        for _ in range(5):
            for addr in jumble(self.bus_addrs):

                operation = choice(["read", "write"])
                if operation == "read":
                    yield from self.verify_bus_side(addr, self.model[addr])

                elif operation == "write":
                    data_width = self.get_data_width(addr)
                    data = randint(0, (2**data_width) - 1)
                    self.model[addr] = data
                    yield from self.write_bus_side(addr, data)

    def one_user_write_then_one_bus_read(self):
        for user_addr in self.user_addrs:
            # write to user side
            data = randint(0, (2**self.width) - 1)
            yield from self.write_user_side(user_addr, data)

            # verify contents when read out from the bus
            words = value_to_words(data, self.n_mems)
            for i, word in enumerate(words):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                yield from self.verify_bus_side(bus_addr, word)

    def multi_user_write_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for user_addr in jumble(self.user_addrs):

            # write a random number to the user side
            data = randint(0, (2**self.width) - 1)
            yield from self.write_user_side(user_addr, data)

            # convert value to words, and save to self.model
            words = value_to_words(data, self.n_mems)
            for i, word in enumerate(words):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                self.model[bus_addr] = word

        # read out every bus_addr in random order
        for bus_addr in jumble(self.bus_addrs):
            yield from self.verify_bus_side(bus_addr, self.model[bus_addr])

    def rand_bus_reads_rand_user_writes(self):
        # random reads and writes in random orders
        for _ in range(5):
            for user_addr in jumble(self.user_addrs):
                bus_addrs = [
                    self.base_addr + user_addr + (i * self.depth)
                    for i in range(self.n_mems)
                ]

                operation = choice(["read", "write"])

                # read from bus side
                if operation == "read":
                    for bus_addr in bus_addrs:
                        yield from self.verify_bus_side(bus_addr, self.model[bus_addr])

                # write to user side
                elif operation == "write":
                    data = randint(0, (2**self.width) - 1)
                    yield from self.write_user_side(user_addr, data)

                    # save words just written to self.model
                    words = value_to_words(data, self.n_mems)
                    for addr, word in zip(bus_addrs, words):
                        self.model[addr] = word

    def get_data_width(self, addr):
        # this part is a little hard to check since we might have a
        # memory at the end of the address space that's less than
        # 16-bits wide. so we'll have to calculate how wide our
        # memory is

        if addr < self.base_addr + (self.n_full * self.depth):
            return 16
        else:
            return self.width % 16

    def verify_bus_side(self, addr, expected_data):
        yield from verify_register(self.mem_core, addr, expected_data)
        for _ in range(4):
            yield

    def write_bus_side(self, addr, data):
        yield from write_register(self.mem_core, addr, data)
        for _ in range(4):
            yield

    def verify_user_side(self, addr, expected_data):
        yield self.mem_core.user_addr.eq(addr)
        yield

        data = yield (self.mem_core.user_data_out)
        if data != expected_data:
            raise ValueError(
                f"Read from {addr} yielded {data} instead of {expected_data}"
            )

    def write_user_side(self, addr, data):
        yield self.mem_core.user_addr.eq(addr)
        yield self.mem_core.user_data_in.eq(data)
        yield self.mem_core.user_write_enable.eq(1)
        yield
        yield self.mem_core.user_addr.eq(0)
        yield self.mem_core.user_data_in.eq(0)
        yield self.mem_core.user_write_enable.eq(0)


def test_bidirectional():
    mem_core = MemoryCore(
        mode="bidirectional",
        width=23,
        depth=512,
        base_addr=0,
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_bidirectional_testbench():
        yield from tests.bus_addrs_all_zero()

        # Test Bus -> Bus functionality
        yield from tests.user_addrs_all_zero()
        yield from tests.one_bus_write_then_one_bus_read()
        yield from tests.multi_bus_writes_then_multi_bus_reads()
        yield from tests.rand_bus_reads_writes()

        # Test User -> Bus functionality
        yield from tests.one_user_write_then_one_bus_read()
        yield from tests.multi_user_write_then_multi_bus_reads()
        yield from tests.rand_bus_reads_rand_user_writes()

    test_bidirectional_testbench()


def test_fpga_to_host():
    mem_core = MemoryCore(
        mode="fpga_to_host",
        width=23,
        depth=512,
        base_addr=0,
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_fpga_to_host_testbench():
        yield from tests.bus_addrs_all_zero()

        # Test User -> Bus functionality
        yield from tests.one_user_write_then_one_bus_read()
        yield from tests.multi_user_write_then_multi_bus_reads()
        yield from tests.rand_bus_reads_rand_user_writes()

    test_fpga_to_host_testbench()


def test_host_to_fpga():
    mem_core = MemoryCore(
        mode="host_to_fpga",
        width=23,
        depth=512,
        base_addr=0,
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_host_to_fpga_testbench():
        yield from tests.user_addrs_all_zero()
        # yield from tests.one_user_write_then_one_bus_read()
        # yield from tests.multi_user_write_then_multi_bus_reads()
        # yield from tests.rand_bus_reads_rand_user_writes()

    test_host_to_fpga_testbench()


# def test_sweep_core_widths():
#     for i in range(1, 64):
#         verify_mem_core(i, 128, 0)


# def test_random_cores():
#     for _ in range(5):
#         width = randint(0, 512)
#         depth = randint(0, 1024)
#         base_addr = randint(0, 2**16 - 1 - depth)
#         verify_mem_core(width, depth, base_addr)
