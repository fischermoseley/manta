from manta.memory_core import MemoryCore
from manta.utils import *
from random import randint, choice, getrandbits
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

        # A model of what each bus address contains
        self.model = {i: 0 for i in self.bus_addrs}

    def bus_addrs_all_zero(self):
        for addr in self.bus_addrs:
            yield from self.verify_bus_side(addr)

    def user_addrs_all_zero(self):
        for addr in self.user_addrs:
            yield from self.verify_user_side(addr)

    def bus_to_bus_functionality(self):
        # yield from self.one_bus_write_then_one_bus_read()
        # yield from self.multi_bus_writes_then_multi_bus_reads()
        yield from self.rand_bus_writes_rand_bus_reads()

    def user_to_bus_functionality(self):
        # yield from self.one_user_write_then_one_bus_read()
        # yield from self.multi_user_write_then_multi_bus_reads()
        yield from self.rand_user_writes_rand_bus_reads()

    def bus_to_user_functionality(self):
        # yield from self.one_bus_write_then_one_user_read()
        # yield from self.multi_bus_write_then_multi_user_reads()
        yield from self.rand_bus_writes_rand_user_reads()

    def user_to_user_functionality(self):
        # yield from self.one_user_write_then_one_user_read()
        # yield from self.multi_user_write_then_multi_user_read()
        yield from self.rand_user_write_rand_user_read()

    def one_bus_write_then_one_bus_read(self):
        for addr in self.bus_addrs:
            data_width = self.get_data_width(addr)
            data = getrandbits(data_width)

            yield from self.write_bus_side(addr, data)
            yield from self.verify_bus_side(addr)

    def multi_bus_writes_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for addr in jumble(self.bus_addrs):
            data_width = self.get_data_width(addr)
            data = getrandbits(data_width)

            yield from self.write_bus_side(addr, data)

        for addr in jumble(self.bus_addrs):
            yield from self.verify_bus_side(addr)

    def rand_bus_writes_rand_bus_reads(self):
        # random reads and writes in random orders
        for _ in range(5):
            for addr in jumble(self.bus_addrs):

                operation = choice(["read", "write"])
                if operation == "read":
                    yield from self.verify_bus_side(addr)

                elif operation == "write":
                    data_width = self.get_data_width(addr)
                    data = getrandbits(data_width)
                    yield from self.write_bus_side(addr, data)

    def one_user_write_then_one_bus_read(self):
        for user_addr in self.user_addrs:
            # write to user side
            data = getrandbits(self.width)
            yield from self.write_user_side(user_addr, data)

            # verify contents when read out from the bus
            for i in range(self.n_mems):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                yield from self.verify_bus_side(bus_addr)

    def multi_user_write_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for user_addr in jumble(self.user_addrs):

            # write a random number to the user side
            data = getrandbits(self.width)
            yield from self.write_user_side(user_addr, data)

        # read out every bus_addr in random order
        for bus_addr in jumble(self.bus_addrs):
            yield from self.verify_bus_side(bus_addr)

    def rand_user_writes_rand_bus_reads(self):
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
                        yield from self.verify_bus_side(bus_addr)

                # write to user side
                elif operation == "write":
                    data = getrandbits(self.width)
                    yield from self.write_user_side(user_addr, data)

    def one_bus_write_then_one_user_read(self):
        for user_addr in self.user_addrs:
            # Try and set the value at the user address to a given value,
            # by writing to the appropriate memory locaitons on the bus side
            data = getrandbits(self.width)

            words = value_to_words(data, self.n_mems)

            for i, word in enumerate(words):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                yield from self.write_bus_side(bus_addr, word)

            yield from self.verify_user_side(user_addr)

    def multi_bus_write_then_multi_user_reads(self):
        # write-write-write then read-read-read
        for bus_addr in jumble(self.bus_addrs):
            data_width = self.get_data_width(bus_addr)
            data = getrandbits(data_width)

            yield from self.write_bus_side(bus_addr, data)

        for user_addr in jumble(self.user_addrs):
            yield from self.verify_user_side(user_addr)

    def rand_bus_writes_rand_user_reads(self):
        for _ in range(5 * self.depth):
            operation = choice(["read", "write"])

            # write random data to random bus address
            if operation == "write":
                bus_addr = randint(self.base_addr, self.max_addr - 1)
                data_width = self.get_data_width(bus_addr)
                data = getrandbits(data_width)

                yield from self.write_bus_side(bus_addr, data)

            # read from random user_addr
            if operation == "read":
                user_addr = randint(0, self.depth - 1)
                yield from self.verify_user_side(user_addr)

    def one_user_write_then_one_user_read(self):
        for addr in self.user_addrs:
            data = getrandbits(self.width)

            yield from self.write_user_side(addr, data)
            yield from self.verify_user_side(addr)

    def multi_user_write_then_multi_user_read(self):
        # write-write-write then read-read-read
        for user_addr in jumble(self.user_addrs):
            data = getrandbits(self.width)
            yield from self.write_user_side(user_addr, data)

        for user_addr in jumble(self.user_addrs):
            yield from self.verify_user_side(user_addr)

    def rand_user_write_rand_user_read(self):
        # random reads and writes in random orders
        for _ in range(5):
            for user_addr in jumble(self.user_addrs):

                operation = choice(["read", "write"])
                if operation == "read":
                    yield from self.verify_user_side(user_addr)

                elif operation == "write":
                    data = getrandbits(self.width)
                    yield from self.write_user_side(user_addr, data)

    def get_data_width(self, addr):
        # this part is a little hard to check since we might have a
        # memory at the end of the address space that's less than
        # 16-bits wide. so we'll have to calculate how wide our
        # memory is

        if addr < self.base_addr + (self.n_full * self.depth):
            return 16
        else:
            return self.width % 16

    def verify_bus_side(self, addr):
        yield from verify_register(self.mem_core, addr, self.model[addr])
        for _ in range(4):
            yield

    def write_bus_side(self, addr, data):
        self.model[addr] = data
        yield from write_register(self.mem_core, addr, data)
        for _ in range(4):
            yield

    def verify_user_side(self, addr):
        # Determine the expected value on the user side by looking
        # up the appropriate bus addresses in the model

        # Convert to bus addresses:
        bus_words = []
        for i in range(self.n_mems):
            bus_addr = self.base_addr + addr + (i * self.depth)
            bus_words.append(self.model[bus_addr])

        expected_data = words_to_value(bus_words)

        yield self.mem_core.user_addr.eq(addr)
        yield
        yield

        data = yield (self.mem_core.user_data_out)
        if data != expected_data:
            raise ValueError(
                f"Read from {addr} yielded {data} instead of {expected_data}"
            )

    def write_user_side(self, addr, data):
        # convert value to words, and save to self.model
        words = value_to_words(data, self.n_mems)
        for i, word in enumerate(words):
            bus_addr = self.base_addr + addr + (i * self.depth)
            self.model[bus_addr] = word

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
        yield from tests.user_addrs_all_zero()

        yield from tests.bus_to_bus_functionality()
        yield from tests.user_to_bus_functionality()
        yield from tests.bus_to_user_functionality()
        yield from tests.user_to_user_functionality()

    test_bidirectional_testbench()


def test_bidirectional_random():
    mem_core = MemoryCore(
        mode="bidirectional",
        width=randint(0, 128),
        depth=randint(0, 1024),
        base_addr=randint(0, 32678),
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_bidirectional_random_testbench():
        yield from tests.bus_addrs_all_zero()
        yield from tests.user_addrs_all_zero()

        yield from tests.bus_to_bus_functionality()
        yield from tests.user_to_bus_functionality()
        yield from tests.bus_to_user_functionality()
        yield from tests.user_to_user_functionality()

    test_bidirectional_random_testbench()


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
        yield from tests.user_to_bus_functionality()

    test_fpga_to_host_testbench()


def test_fpga_to_host_random():
    mem_core = MemoryCore(
        mode="fpga_to_host",
        width=randint(0, 128),
        depth=randint(0, 1024),
        base_addr=randint(0, 32678),
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_fpga_to_host_random_testbench():
        yield from tests.bus_addrs_all_zero()
        yield from tests.user_to_bus_functionality()

    test_fpga_to_host_random_testbench()


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
        yield from tests.bus_to_user_functionality()

    test_host_to_fpga_testbench()


def test_host_to_fpga_random():
    mem_core = MemoryCore(
        mode="host_to_fpga",
        width=randint(0, 128),
        depth=randint(0, 1024),
        base_addr=randint(0, 32678),
        interface=None,
    )

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    def test_host_to_fpga_random_testbench():
        yield from tests.user_addrs_all_zero()
        yield from tests.bus_to_user_functionality()

    test_host_to_fpga_random_testbench()
