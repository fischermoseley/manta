from manta.memory_core import MemoryCore
from manta.utils import *
from random import randint, sample, choice

width = 18
depth = 512
base_addr = 0
mem_core = MemoryCore(
    mode="bidirectional", width=width, depth=depth, base_addr=base_addr, interface=None
)

max_addr = mem_core.get_max_addr()
bus_addrs = list(range(base_addr, max_addr))  # include the endpoint!
user_addrs = list(range(depth))


@simulate(mem_core)
def test_bidirectional():
    # make sure each address on the bus side contains zero
    for addr in bus_addrs:
        yield from verify_register(mem_core, addr, 0)

    # make sure each address on the user side contains zero
    for addr in user_addrs:
        yield from verify_user_side(mem_core, addr, 0)

    # write then immediately read
    for addr in bus_addrs:
        # this part is a little hard to check since we might have a
        # memory at the end of the address space that's less than
        # 16-bits wide. so we'll have to calculate how wide our
        # memory is

        n_full = width // 16
        if addr < base_addr + (n_full * depth):
            data_width = 16
        else:
            data_width = width % 16

        data = randint(0, (2**data_width) - 1)
        yield from write_register(mem_core, addr, data)
        yield
        yield
        yield
        yield
        yield from verify_register(mem_core, addr, data)
        yield
        yield
        yield
        yield
        yield

    # write-write-write then read-read-read
    model = {}
    for addr in sample(bus_addrs, len(bus_addrs)):
        n_full = width // 16
        if addr < base_addr + (n_full * depth):
            data_width = 16
        else:
            data_width = width % 16

        data = randint(0, (2**data_width) - 1)
        model[addr] = data
        yield from write_register(mem_core, addr, data)
        yield
        yield
        yield
        yield

    for addr in sample(bus_addrs, len(bus_addrs)):
        yield from verify_register(mem_core, addr, model[addr])
        yield
        yield
        yield
        yield

    # random reads and writes in random orders
    for _ in range(5):
        for addr in sample(bus_addrs, len(bus_addrs)):

            operation = choice(["read", "write"])
            if operation == "read":
                yield from verify_register(mem_core, addr, model[addr])
                yield
                yield
                yield
                yield
                yield
                yield

            elif operation == "write":
                n_full = width // 16

                if addr < base_addr + (n_full * depth):
                    data_width = 16
                else:
                    data_width = width % 16

                data = randint(0, (2**data_width) - 1)
                model[addr] = data

                yield from write_register(mem_core, addr, data)
                yield
                yield
                yield
                yield
                yield
                yield


def verify_user_side(mem_core, addr, expected_data):
    yield mem_core.user_addr.eq(addr)
    yield mem_core.user_write_enable.eq(0)
    yield

    data = yield (mem_core.user_data_out)
    if data != expected_data:
        raise ValueError(f"Read from {addr} yielded {data} instead of {expected_data}")


# def fill_mem_from_user_port(mem_core, depth):
#     for i in range(depth):
#         yield mem_core.user_addr.eq(i)
#         yield mem_core.user_data_in.eq(i)
#         yield mem_core.user_write_enable.eq(1)
#         yield

#     yield mem_core.user_write_enable.eq(0)
#     yield


# def verify_mem_core(width, depth, base_addr):
#     mem_core = MemoryCore("bidirectional", width, depth, base_addr, interface=None)

#     def testbench():
#         yield from fill_mem_from_user_port(mem_core, depth)

#         # Read from address sequentially
#         for i in range(depth):
#             yield from verify_register(mem_core, i + base_addr, i % (2**width))

#         # Read from addresses randomly
#         for i in sample(range(depth), k=depth):
#             yield from verify_register(mem_core, i + base_addr, i % (2**width))

#     simulate(mem_core, testbench)

# def test_sweep_core_widths():
#     for i in range(1, 64):
#         verify_mem_core(i, 128, 0)


# def test_random_cores():
#     for _ in range(5):
#         width = randint(0, 512)
#         depth = randint(0, 1024)
#         base_addr = randint(0, 2**16 - 1 - depth)
#         verify_mem_core(width, depth, base_addr)
