from amaranth.sim import Simulator
from manta.io_core import IOCore
from manta.utils import *
from random import randint

config = {
    "type": "io",
    "inputs": {"probe0": 1, "probe1": 2, "probe2": 8, "probe3": 20},
    "outputs": {
        "probe4": {"width": 1, "initial_value": 1},
        "probe5": {"width": 2, "initial_value": 2},
        "probe6": 8,
        "probe7": {"width": 20, "initial_value": 65538},
    },
}

io_core = IOCore(config, base_addr=0, interface=None)


def pulse_strobe_register():
    strobe_addr = io_core.mmap["strobe"]["addrs"][0]
    yield from write_register(io_core, strobe_addr, 0)
    yield from write_register(io_core, strobe_addr, 1)
    yield from write_register(io_core, strobe_addr, 0)


def test_output_probe_initial_values():
    def testbench():
        # Verify all output probes initialize to the values in the config
        for name, attrs in config["outputs"].items():
            initial_value = 0
            if isinstance(attrs, dict):
                if "initial_value" in attrs:
                    initial_value = attrs["initial_value"]

            output_probe = getattr(io_core, name)
            value = yield output_probe

            if value != initial_value:
                raise ValueError(
                    f"Output probe {name} initialized to {value} instead of {initial_value}"
                )

            else:
                print(f"Output probe {name} initialized to {value} as expected.")

    simulate(io_core, testbench)


def test_input_probe_buffer_initial_value():
    def testbench():
        # Verify all input probe buffers initialize to zero
        for name, width in config["inputs"].items():
            addrs = io_core.mmap[name + "_buf"]["addrs"]

            for addr in addrs:
                yield from verify_register(io_core, addr, 0)

    simulate(io_core, testbench)


def test_output_probe_buffer_initial_value():
    def testbench():
        # Verify all output probe buffers initialize to the values in the config
        for name, attrs in config["outputs"].items():
            addrs = io_core.mmap[name + "_buf"]["addrs"]

            datas = [0] * len(addrs)
            if isinstance(attrs, dict):
                if "initial_value" in attrs:
                    datas = value_to_words(attrs["initial_value"], len(addrs))

            for addr, data in zip(addrs, datas):
                yield from verify_register(io_core, addr, data)

    simulate(io_core, testbench)


def test_output_probes_are_writeable():
    def testbench():
        for name, attrs in config["outputs"].items():
            if isinstance(attrs, dict):
                width = attrs["width"]
            else:
                width = attrs

            addrs = io_core.mmap[name + "_buf"]["addrs"]
            test_value = randint(0, (2**width) - 1)
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
        for name, attrs in config["outputs"].items():
            if isinstance(attrs, dict):
                width = attrs["width"]
            else:
                width = attrs

            addrs = io_core.mmap[name + "_buf"]["addrs"]
            test_value = randint(0, (2**width) - 1)
            datas = value_to_words(test_value, len(addrs))

            # write value to registers
            for addr, data in zip(addrs, datas):
                yield from write_register(io_core, addr, data)

            # pulse strobe register
            yield from pulse_strobe_register()

            # check that outputs took updated value
            output_probe = getattr(io_core, name)
            value = yield (output_probe)

            if value != test_value:
                raise ValueError(
                    f"Output probe {name} took value {value} instead of {test_value} after pulsing strobe."
                )

            else:
                print(f"Output probe {name} took value {value} after pulsing strobe.")

    simulate(io_core, testbench)


def test_input_probes_update():
    def testbench():
        for name, width in config["inputs"].items():
            test_value = randint(0, (2**width) - 1)

            # set input probe value
            input_probe = getattr(io_core, name)
            yield input_probe.eq(test_value)

            # pulse strobe register
            yield from pulse_strobe_register()

            # check that values are as expected once read back
            addrs = io_core.mmap[name + "_buf"]["addrs"]
            datas = value_to_words(test_value, len(addrs))

            for addr, data in zip(addrs, datas):
                yield from verify_register(io_core, addr, data)

    simulate(io_core, testbench)
