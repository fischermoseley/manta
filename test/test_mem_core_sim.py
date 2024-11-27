from math import ceil
from random import choice, getrandbits, randint

import pytest

from manta.memory_core import MemoryCore
from manta.utils import *


class MemoryCoreTests:
    def __init__(self, mem_core):
        self.mem_core = mem_core
        self.base_addr = mem_core.base_addr
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

    def set_simulation_context(self, ctx):
        self.ctx = ctx

    async def bus_addrs_all_zero(self):
        for addr in self.bus_addrs:
            await self.verify_bus_side(addr)

    async def user_addrs_all_zero(self):
        for addr in self.user_addrs:
            await self.verify_user_side(addr)

    async def bus_to_bus_functionality(self):
        await self.one_bus_write_then_one_bus_read()
        await self.multi_bus_writes_then_multi_bus_reads()
        await self.rand_bus_writes_rand_bus_reads()

    async def user_to_bus_functionality(self):
        await self.one_user_write_then_one_bus_read()
        await self.multi_user_write_then_multi_bus_reads()
        await self.rand_user_writes_rand_bus_reads()

    async def bus_to_user_functionality(self):
        await self.one_bus_write_then_one_user_read()
        await self.multi_bus_write_then_multi_user_reads()
        await self.rand_bus_writes_rand_user_reads()

    async def user_to_user_functionality(self):
        await self.one_user_write_then_one_user_read()
        await self.multi_user_write_then_multi_user_read()
        await self.rand_user_write_rand_user_read()

    async def one_bus_write_then_one_bus_read(self):
        for addr in self.bus_addrs:
            data_width = self.get_data_width(addr)
            data = getrandbits(data_width)

            await self.write_bus_side(addr, data)
            await self.verify_bus_side(addr)

    async def multi_bus_writes_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for addr in jumble(self.bus_addrs):
            data_width = self.get_data_width(addr)
            data = getrandbits(data_width)

            await self.write_bus_side(addr, data)

        for addr in jumble(self.bus_addrs):
            await self.verify_bus_side(addr)

    async def rand_bus_writes_rand_bus_reads(self):
        # random reads and writes in random orders
        for _ in range(5):
            for addr in jumble(self.bus_addrs):
                operation = choice(["read", "write"])
                if operation == "read":
                    await self.verify_bus_side(addr)

                elif operation == "write":
                    data_width = self.get_data_width(addr)
                    data = getrandbits(data_width)
                    await self.write_bus_side(addr, data)

    async def one_user_write_then_one_bus_read(self):
        for user_addr in self.user_addrs:
            # write to user side
            data = getrandbits(self.width)
            await self.write_user_side(user_addr, data)

            # verify contents when read out from the bus
            for i in range(self.n_mems):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                await self.verify_bus_side(bus_addr)

    async def multi_user_write_then_multi_bus_reads(self):
        # write-write-write then read-read-read
        for user_addr in jumble(self.user_addrs):
            # write a random number to the user side
            data = getrandbits(self.width)
            await self.write_user_side(user_addr, data)

        # read out every bus_addr in random order
        for bus_addr in jumble(self.bus_addrs):
            await self.verify_bus_side(bus_addr)

    async def rand_user_writes_rand_bus_reads(self):
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
                        await self.verify_bus_side(bus_addr)

                # write to user side
                elif operation == "write":
                    data = getrandbits(self.width)
                    await self.write_user_side(user_addr, data)

    async def one_bus_write_then_one_user_read(self):
        for user_addr in self.user_addrs:
            # Try and set the value at the user address to a given value,
            # by writing to the appropriate memory locations on the bus side
            data = getrandbits(self.width)

            words = value_to_words(data, self.n_mems)

            for i, word in enumerate(words):
                bus_addr = self.base_addr + user_addr + (i * self.depth)
                await self.write_bus_side(bus_addr, word)

            await self.verify_user_side(user_addr)

    async def multi_bus_write_then_multi_user_reads(self):
        # write-write-write then read-read-read
        for bus_addr in jumble(self.bus_addrs):
            data_width = self.get_data_width(bus_addr)
            data = getrandbits(data_width)

            await self.write_bus_side(bus_addr, data)

        for user_addr in jumble(self.user_addrs):
            await self.verify_user_side(user_addr)

    async def rand_bus_writes_rand_user_reads(self):
        for _ in range(5 * self.depth):
            operation = choice(["read", "write"])

            # write random data to random bus address
            if operation == "write":
                bus_addr = randint(self.base_addr, self.max_addr - 1)
                data_width = self.get_data_width(bus_addr)
                data = getrandbits(data_width)

                await self.write_bus_side(bus_addr, data)

            # read from random user_addr
            if operation == "read":
                user_addr = randint(0, self.depth - 1)
                await self.verify_user_side(user_addr)

    async def one_user_write_then_one_user_read(self):
        for addr in self.user_addrs:
            data = getrandbits(self.width)

            await self.write_user_side(addr, data)
            await self.verify_user_side(addr)

    async def multi_user_write_then_multi_user_read(self):
        # write-write-write then read-read-read
        for user_addr in jumble(self.user_addrs):
            data = getrandbits(self.width)
            await self.write_user_side(user_addr, data)

        for user_addr in jumble(self.user_addrs):
            await self.verify_user_side(user_addr)

    async def rand_user_write_rand_user_read(self):
        # random reads and writes in random orders
        for _ in range(5):
            for user_addr in jumble(self.user_addrs):
                operation = choice(["read", "write"])
                if operation == "read":
                    await self.verify_user_side(user_addr)

                elif operation == "write":
                    data = getrandbits(self.width)
                    await self.write_user_side(user_addr, data)

    def get_data_width(self, addr):
        # this part is a little hard to check since we might have a
        # memory at the end of the address space that's less than
        # 16-bits wide. so we'll have to calculate how wide our
        # memory is

        if addr < self.base_addr + (self.n_full * self.depth):
            return 16
        else:
            return self.width % 16

    async def verify_bus_side(self, addr):
        await verify_register(self.mem_core, self.ctx, addr, self.model[addr])
        await self.ctx.tick().repeat(4)

    async def write_bus_side(self, addr, data):
        self.model[addr] = data
        await write_register(self.mem_core, self.ctx, addr, data)
        await self.ctx.tick().repeat(4)

    async def verify_user_side(self, addr):
        # Determine the expected value on the user side by looking
        # up the appropriate bus addresses in the model

        # Convert to bus addresses:
        bus_words = []
        for i in range(self.n_mems):
            bus_addr = self.base_addr + addr + (i * self.depth)
            bus_words.append(self.model[bus_addr])

        expected_data = words_to_value(bus_words)

        self.ctx.set(self.mem_core.user_addr, addr)
        await self.ctx.tick().repeat(2)

        data = self.ctx.get(self.mem_core.user_data_out)
        if data != expected_data:
            raise ValueError(
                f"Read from {addr} yielded {data} instead of {expected_data}"
            )

    async def write_user_side(self, addr, data):
        # convert value to words, and save to self.model
        words = value_to_words(data, self.n_mems)
        for i, word in enumerate(words):
            bus_addr = self.base_addr + addr + (i * self.depth)
            self.model[bus_addr] = word

        self.ctx.set(self.mem_core.user_addr, addr)
        self.ctx.set(self.mem_core.user_data_in, data)
        self.ctx.set(self.mem_core.user_write_enable, 1)
        await self.ctx.tick()
        self.ctx.set(self.mem_core.user_addr, 0)
        self.ctx.set(self.mem_core.user_data_in, 0)
        self.ctx.set(self.mem_core.user_write_enable, 0)


modes = ["bidirectional", "fpga_to_host", "host_to_fpga"]
widths = [23, randint(0, 128)]
depths = [512, randint(0, 1024)]
base_addrs = [0, randint(0, 32678)]

cases = [
    (m, w, d, ba) for m in modes for w in widths for d in depths for ba in base_addrs
]


@pytest.mark.parametrize("mode, width, depth, base_addr", cases)
def test_mem_core(mode, width, depth, base_addr):
    mem_core = MemoryCore(mode, width, depth)
    mem_core.base_addr = base_addr

    tests = MemoryCoreTests(mem_core)

    @simulate(mem_core)
    async def testbench(ctx):
        tests.set_simulation_context(ctx)

        if mode == "bidirectional":
            await tests.bus_addrs_all_zero()
            await tests.user_addrs_all_zero()

            await tests.bus_to_bus_functionality()
            await tests.user_to_bus_functionality()
            await tests.bus_to_user_functionality()
            await tests.user_to_user_functionality()

        if mode == "fpga_to_host":
            await tests.bus_addrs_all_zero()
            await tests.user_to_bus_functionality()

        if mode == "host_to_fpga":
            await tests.user_addrs_all_zero()
            await tests.bus_to_user_functionality()

    testbench()
