from amaranth import *
from amaranth.sim import Simulator
from manta.io_core import IOCore
from manta.utils import *
from random import randint

probe0 = Signal(1)
probe1 = Signal(2)
probe2 = Signal(8)
probe3 = Signal(20)
inputs = [probe0, probe1, probe2, probe3]

probe4 = Signal(1, reset=1)
probe5 = Signal(2, reset=2)
probe6 = Signal(8)
probe7 = Signal(20, reset=65538)
outputs = [probe4, probe5, probe6, probe7]

io_core = IOCore(base_addr=0, interface=None, inputs=inputs, outputs=outputs)


def pulse_strobe_register():
    strobe_addr = io_core._memory_map["strobe"]["addrs"][0]
    yield from write_register(io_core, strobe_addr, 0)
    yield from write_register(io_core, strobe_addr, 1)
    yield from write_register(io_core, strobe_addr, 0)


def test_input_probe_buffer_initial_value():
    def testbench():
        # Verify all input probe buffers initialize to zero
        for i in inputs:
            addrs = io_core._memory_map[i.name]["addrs"]

            for addr in addrs:
                yield from verify_register(io_core, addr, 0)

    simulate(io_core, testbench)


def test_output_probe_buffer_initial_value():
    def testbench():
        # Verify all output probe buffers initialize to the values in the config
        for o in outputs:
            addrs = io_core._memory_map[o.name]["addrs"]
            datas = value_to_words(o.reset, len(addrs))

            for addr, data in zip(addrs, datas):
                yield from verify_register(io_core, addr, data)

    simulate(io_core, testbench)


def test_output_probes_are_writeable():
    def testbench():
        for o in outputs:
            addrs = io_core._memory_map[o.name]["addrs"]
            test_value = randint(0, (2**o.width) - 1)
            datas = value_to_words(test_value, len(addrs))

            # write value to registers
            for addr, data in zip(addrs, datas):
                yield from write_register(io_core, addr, data)

            # read value back from registers
            for addr, data in zip(addrs, datas):
                yield from verify_register(io_core, addr, data)

    simulate(io_core, testbench)


def test_output_probes_update():
    def testbench():
        for o in outputs:
            addrs = io_core._memory_map[o.name]["addrs"]
            test_value = randint(0, (2**o.width) - 1)
            datas = value_to_words(test_value, len(addrs))

            # write value to registers
            for addr, data in zip(addrs, datas):
                yield from write_register(io_core, addr, data)

            # pulse strobe register
            yield from pulse_strobe_register()

            # check that outputs took updated value
            value = yield (o)

            if value != test_value:
                raise ValueError(
                    f"Output probe {o.name} took value {value} instead of {test_value} after pulsing strobe."
                )

            else:
                print(f"Output probe {o.name} took value {value} after pulsing strobe.")

    simulate(io_core, testbench)


def test_input_probes_update():
    def testbench():
        for i in inputs:
            # set input probe value
            test_value = randint(0, (2**i.width) - 1)
            yield i.eq(test_value)

            # pulse strobe register
            yield from pulse_strobe_register()

            # check that values are as expected once read back
            addrs = io_core._memory_map[i.name]["addrs"]
            datas = value_to_words(test_value, len(addrs))

            for addr, data in zip(addrs, datas):
                yield from verify_register(io_core, addr, data)

    simulate(io_core, testbench)
