from manta.memory_core import MemoryCore
from manta.utils import *
from random import randint, sample


def fill_mem_from_user_port(mem_core, depth):
    for i in range(depth):
        yield mem_core.user_addr.eq(i)
        yield mem_core.user_data_in.eq(i)
        yield mem_core.user_write_enable.eq(1)
        yield

    yield mem_core.user_write_enable.eq(0)
    yield


def verify_mem_core(width, depth, base_addr):
    mem_core = MemoryCore("fpga_to_host", width, depth, base_addr, interface=None)

    def testbench():
        yield from fill_mem_from_user_port(mem_core, depth)

        # Read from address sequentially
        for i in range(depth):
            yield from verify_register(mem_core, i + base_addr, i % (2**width))

        # Read from addresses randomly
        for i in sample(range(depth), k=depth):
            yield from verify_register(mem_core, i + base_addr, i % (2**width))

    simulate(mem_core, testbench)


def test_sweep_core_widths():
    for i in range(1, 64):
        verify_mem_core(i, 128, 0)


def test_random_cores():
    for _ in range(5):
        width = randint(0, 512)
        depth = randint(0, 1024)
        base_addr = randint(0, 2**16 - 1 - depth)
        verify_mem_core(width, depth, base_addr)
