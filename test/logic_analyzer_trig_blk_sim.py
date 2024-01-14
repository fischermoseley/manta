from amaranth import *
from amaranth.sim import Simulator
from manta.logic_analyzer import LogicAnalyzerTriggerBlock
from manta.utils import *
from random import randint, sample


# Make random number of random width probes
probes = [Signal(randint(1, 32), name=str(i)) for i in range(randint(1, 32))]
trig_blk = LogicAnalyzerTriggerBlock(probes, base_addr=0, interface=None)


def write_trig_blk_register(name, value):
    strobe_addr = trig_blk.r.base_addr
    yield from write_register(trig_blk, strobe_addr, 0)

    addrs = trig_blk.r.mmap[f"{name}_buf"]["addrs"]
    datas = value_to_words(value, len(addrs))
    for addr, data in zip(addrs, datas):
        yield from write_register(trig_blk, addr, data)

    yield from write_register(trig_blk, strobe_addr, 1)
    yield from write_register(trig_blk, strobe_addr, 0)


def test():
    def testbench():
        # Step through each probe and perform all functions in random order
        for p in trig_blk.probes:
            ops = trig_blk.triggers[0].operations
            for op in sample(list(ops.keys()), len(ops)):
                # Program operation register with selected register
                yield from write_trig_blk_register(f"{p.name}_op", ops[op])

                if op == "DISABLE":
                    # Argument can be anything, since it's not used for this operation
                    yield from write_trig_blk_register(
                        f"{p.name}_arg", randint(0, (2**p.width) - 1)
                    )
                    yield p.eq(randint(0, (2**p.width) - 1))
                    yield

                    if (yield trig_blk.trig):
                        raise ValueError("Trigger raised when disabled!")

                if op == "RISING":
                    # Argument can be anything, since it's not used for this operation
                    yield from write_trig_blk_register(
                        f"{p.name}_arg", randint(0, (2**p.width) - 1)
                    )
                    yield p.eq(0)
                    yield
                    yield p.eq(randint(1, (2**p.width) - 1))
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")

                if op == "FALLING":
                    # Argument can be anything, since it's not used for this operation
                    yield from write_trig_blk_register(
                        f"{p.name}_arg", randint(0, (2**p.width) - 1)
                    )
                    yield p.eq(randint(1, (2**p.width) - 1))
                    yield
                    yield p.eq(0)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "CHANGING":
                    # Argument can be anything, since it's not used for this operation
                    yield from write_trig_blk_register(
                        f"{p.name}_arg", randint(0, (2**p.width) - 1)
                    )
                    yield p.eq(randint(1, (2**p.width) - 1))
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "GT":
                    upper = randint(1, (2**p.width) - 1)
                    lower = randint(0, upper - 1)

                    yield from write_trig_blk_register(f"{p.name}_arg", lower)
                    yield p.eq(upper)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "LT":
                    upper = randint(1, (2**p.width) - 1)
                    lower = randint(0, upper - 1)

                    yield from write_trig_blk_register(f"{p.name}_arg", upper)
                    yield p.eq(lower)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "GEQ":
                    upper = randint(1, (2**p.width) - 1)
                    lower = randint(0, upper - 1)

                    # test that the case where it's equal
                    yield from write_trig_blk_register(f"{p.name}_arg", lower)
                    yield p.eq(lower)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                    # test the case where it's greater than
                    yield p.eq(upper)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "LEQ":
                    upper = randint(1, (2**p.width) - 1)
                    lower = randint(0, upper - 1)

                    # test that the case where it's equal
                    yield from write_trig_blk_register(f"{p.name}_arg", upper)
                    yield p.eq(upper)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                    # test the case where it's less than
                    yield p.eq(lower)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "EQ":
                    value = randint(0, (2**p.width) - 1)
                    yield from write_trig_blk_register(f"{p.name}_arg", value)
                    yield p.eq(value)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass

                if op == "NEQ":
                    upper = randint(1, (2**p.width) - 1)
                    lower = randint(0, upper - 1)

                    # test that the case where it's equal
                    yield from write_trig_blk_register(f"{p.name}_arg", upper)
                    yield p.eq(lower)
                    yield

                    if not (yield trig_blk.trig):
                        raise ValueError(f"Trigger not raised on probe {p.name}!")
                    pass


                # disable probe once complete
                yield
                yield from write_trig_blk_register(f"{p.name}_op", ops["DISABLE"])
                yield from write_trig_blk_register(f"{p.name}_arg", 0)
                yield p.eq(0)

    simulate(trig_blk, testbench, "out.vcd")
