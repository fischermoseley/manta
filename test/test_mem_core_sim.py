from manta.memory_core import MemoryCore
from manta.utils import *
from random import randint, sample, choice


class MemoryCoreTests:
    def __init__(self, mem_core):
        self.mem_core = mem_core
        self.base_addr = mem_core._base_addr
        self.max_addr = mem_core.max_addr
        self.width = self.mem_core._width
        self.depth = self.mem_core._depth

        self.bus_addrs = list(
            range(self.base_addr, self.max_addr)
        )  # include the endpoint!
        self.user_addrs = list(range(self.mem_core._depth))
        self.model = {}

    def check_each_address_on_bus_side_contains_zero(self):
        for addr in self.bus_addrs:
            yield from self.verify_bus_side(addr, 0)

    def check_each_address_on_user_side_contains_zero(self):
        for addr in self.user_addrs:
            yield from self.verify_user_side(addr, 0)

    def check_write_then_immediately_read_bus_side(self):
        for addr in self.bus_addrs:
            # this part is a little hard to check since we might have a
            # memory at the end of the address space that's less than
            # 16-bits wide. so we'll have to calculate how wide our
            # memory is

            data_width = self.get_data_width(addr)
            data = randint(0, (2**data_width) - 1)

            yield from self.write_bus_side(addr, data)
            yield from self.verify_bus_side(addr, data)

    def check_multiple_writes_then_multiple_reads(self):
        # write-write-write then read-read-read
        for addr in sample(self.bus_addrs, len(self.bus_addrs)):
            data_width = self.get_data_width(addr)
            data = randint(0, (2**data_width) - 1)

            self.model[addr] = data
            yield from self.write_bus_side(addr, data)

        for addr in sample(self.bus_addrs, len(self.bus_addrs)):
            yield from self.verify_bus_side(addr, self.model[addr])

    def check_random_reads_random_writes_random_orders(self):
        # random reads and writes in random orders
        for _ in range(5):
            for addr in sample(self.bus_addrs, len(self.bus_addrs)):

                operation = choice(["read", "write"])
                if operation == "read":
                    yield from self.verify_bus_side(addr, self.model[addr])

                elif operation == "write":
                    data_width = self.get_data_width(addr)
                    data = randint(0, (2**data_width) - 1)
                    self.model[addr] = data
                    yield from self.write_bus_side(addr, data)

    def get_data_width(self, addr):
        n_full = self.width // 16
        if addr < self.base_addr + (n_full * self.depth):
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
        yield self.mem_core.user_write_enable.eq(0)
        yield

        data = yield (self.mem_core.user_data_out)
        if data != expected_data:
            raise ValueError(
                f"Read from {addr} yielded {data} instead of {expected_data}"
            )


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
    yield from tests.check_each_address_on_bus_side_contains_zero()
    yield from tests.check_each_address_on_user_side_contains_zero()
    yield from tests.check_write_then_immediately_read_bus_side()
    yield from tests.check_multiple_writes_then_multiple_reads()
    yield from tests.check_random_reads_random_writes_random_orders()


# def test_sweep_core_widths():
#     for i in range(1, 64):
#         verify_mem_core(i, 128, 0)


# def test_random_cores():
#     for _ in range(5):
#         width = randint(0, 512)
#         depth = randint(0, 1024)
#         base_addr = randint(0, 2**16 - 1 - depth)
#         verify_mem_core(width, depth, base_addr)
