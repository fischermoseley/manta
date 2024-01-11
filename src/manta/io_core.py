from amaranth import *
from warnings import warn
from .utils import *
from math import ceil


class IOCore(Elaboratable):
    """
    Contains the HDL to instantiate an IO core on a FPGA, and the functions to interact with it. For
    more information on the core itself, check out the IO core documentation.
    """

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.base_addr = base_addr
        self.interface = interface

        self.check_config(self.config)
        self.define_signals()
        self.mmap, self.max_addr = self.assign_memory()

    def check_config(self, config):
        # make sure ports are defined
        if "inputs" not in config and "outputs" not in config:
            raise ValueError("No input or output ports specified.")

        # check for unrecognized options
        valid_options = ["type", "inputs", "outputs", "user_clock"]
        for option in config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in IO core.'")

        # check that user_clock is a bool
        if "user_clock" in config:
            if not isinstance(config["user_clock"], bool):
                raise ValueError("Option user_clock must be a boolean.")

        # check that inputs is only dicts of format name:width
        if "inputs" in config:
            for name, attrs in config["inputs"].items():
                if not isinstance(name, str):
                    raise ValueError(
                        f'Input probe "{name}" has invalid name, names must be strings.'
                    )

                if not isinstance(attrs, int):
                    raise ValueError(f'Input probe "{name}" must have integer width.')

                if not attrs > 0:
                    raise ValueError(f'Input probe "{name}" must have positive width.')

        if "outputs" in config:
            for name, attrs in config["outputs"].items():
                if not isinstance(name, str):
                    raise ValueError(
                        f'Output probe "{name}" has invalid name, names must be strings.'
                    )

                if not isinstance(attrs, int) and not isinstance(attrs, dict):
                    raise ValueError(f'Unrecognized format for output probe "{name}".')

                if isinstance(attrs, int):
                    if not attrs > 0:
                        raise ValueError(
                            f'Output probe "{name}" must have positive width.'
                        )

                if isinstance(attrs, dict):
                    # check that each output probe has only recognized options
                    valid_options = ["width", "initial_value"]
                    for option in attrs:
                        if option not in valid_options:
                            warn(f'Ignoring unrecognized option "{option}" in IO core.')

                    # check that widths are appropriate
                    if "width" not in attrs:
                        raise ValueError(f"No width specified for output probe {name}.")

                    if not isinstance(attrs["width"], int):
                        raise ValueError(
                            f'Output probe "{name}" must have integer width.'
                        )

                    if not attrs["width"] > 0:
                        raise ValueError(
                            f'Input probe "{name}" must have positive width.'
                        )

    def define_signals(self):
        # Bus Input/Output
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        # Input Probes (and buffers)
        if "inputs" in self.config:
            for name, width in self.config["inputs"].items():
                setattr(self, name, Signal(width, name=name))
                setattr(self, name + "_buf", Signal(width, name=name + "_buf"))

        # Output Probes (and buffers)
        if "outputs" in self.config:
            for name, attrs in self.config["outputs"].items():
                if isinstance(attrs, dict):
                    width = attrs["width"]
                    initial_value = attrs["initial_value"]
                else:
                    width = attrs
                    initial_value = 0

                setattr(self, name, Signal(width, name=name, reset=initial_value))
                setattr(
                    self,
                    name + "_buf",
                    Signal(width, name=name + "_buf", reset=initial_value),
                )

        # Strobe Register
        self.strobe = Signal(reset=0)

    def assign_memory(self):
        """
        the memory map is a dict that maps registers (in memory) to their locations (in memory)
        as well as their Signals (from Amaranth). This looks like the following:

        {
            strobe:
                addrs: [0x0000]
                signals: [self.strobe]
            probe0_buf:
                addrs: [0x0001]
                signals: [self.probe0_buf]
            probe1_buf:
                addrs: [0x0002]
                signals: [self.probe1_buf]
            probe2_buf:
                addrs: [0x0003]
                signals: [self.probe2_buf]
            probe3_buf:
                addrs: [0x0004, 0x0005]
                signals: [self.probe3_buf[0:15], self.probe3_buf[16:19]]
            ... and so on
        }

        """
        mmap = {}

        # Add strobe register first
        mmap["strobe"] = dict(addrs=[self.base_addr], signals=[self.strobe])

        # Add all input and output probes
        all_probes = {}
        if "inputs" in self.config:
            all_probes = {**all_probes, **self.config["inputs"]}

        if "outputs" in self.config:
            all_probes = {**all_probes, **self.config["outputs"]}

        for name, attrs in all_probes.items():
            # Handle output probes that might have initial value specified in addition to width
            if isinstance(attrs, dict):
                width = attrs["width"]
            else:
                width = attrs

            # Assign addresses
            last_used_addr = list(mmap.values())[-1]["addrs"][-1]
            addrs = [last_used_addr + 1 + i for i in range(ceil(width / 16))]

            # Slice signal into 16-bit chunks
            signal = getattr(self, name + "_buf")
            signals = [signal[16 * i : 16 * (i + 1)] for i in range(ceil(width / 16))]

            mmap[name + "_buf"] = {"addrs": addrs, "signals": signals}

        # Compute maximum address used by the core
        max_addr = list(mmap.values())[-1]["addrs"][-1]
        return mmap, max_addr

    def elaborate(self, platform):
        m = Module()

        # Shuffle bus transactions along
        m.d.sync += self.bus_o.eq(self.bus_i)

        # Update buffers from probes
        with m.If(self.strobe):
            # Input buffers
            if "inputs" in self.config:
                for name in self.config["inputs"]:
                    input_probe = getattr(self, name)
                    input_probe_buf = getattr(self, name + "_buf")
                    m.d.sync += input_probe_buf.eq(input_probe)

            # Output buffers
            if "outputs" in self.config:
                for name in self.config["outputs"]:
                    output_probe = getattr(self, name)
                    output_probe_buf = getattr(self, name + "_buf")
                    m.d.sync += output_probe.eq(output_probe_buf)

        # Handle register reads and writes
        with m.If((self.bus_i.addr >= self.base_addr)):
            with m.If((self.bus_o.addr <= self.max_addr)):
                for entry in self.mmap.values():
                    for addr, signal in zip(entry["addrs"], entry["signals"]):
                        with m.If(self.bus_i.rw):
                            with m.If(self.bus_i.addr == addr):
                                m.d.sync += signal.eq(self.bus_i.data)

                        with m.Else():
                            with m.If(self.bus_i.addr == addr):
                                m.d.sync += self.bus_o.data.eq(signal)

        return m

    def get_top_level_ports(self):
        ports = []
        for name in self.config["inputs"].keys():
            ports.append(getattr(self, name))

        for name in self.config["outputs"].keys():
            ports.append(getattr(self, name))

        return ports

    def get_max_addr(self):
        return self.max_addr

    def set_probe(self, probe_name, value):
        # check that probe is an output probe
        if probe_name not in self.config["outputs"]:
            raise ValueError(f"Output probe '{probe_name}' not found.")

        # check that value is an integer
        if not isinstance(value, int):
            raise ValueError("Value must be an integer.")

        # get the width of the probe, make sure value isn't too large for the probe
        attrs = self.config["outputs"][probe_name]
        if isinstance(attrs, int):
            width = attrs

        if isinstance(attrs, dict):
            width = attrs["width"]

        if value > 0 and value > 2**width - 1:
            raise ValueError("Unsigned integer too large.")

        if value < 0 and value < -(2 ** (width - 1)):
            raise ValueError("Signed integer too large.")

        # set value in buffer
        addrs = self.mmap[probe_name + "_buf"]["addrs"]
        datas = value_to_words(value, len(addrs))
        self.interface.write(addrs, datas)

        # pulse strobe register
        strobe_addr = self.mmap["strobe"]["addrs"][0]
        self.interface.write(strobe_addr, 0)
        self.interface.write(strobe_addr, 1)
        self.interface.write(strobe_addr, 0)

    def get_probe(self, probe_name):
        # pulse strobe register
        strobe_addr = self.mmap["strobe"]["addrs"][0]
        self.interface.write(strobe_addr, 0)
        self.interface.write(strobe_addr, 1)
        self.interface.write(strobe_addr, 0)

        # get value from buffer
        addrs = self.mmap[probe_name + "_buf"]["addrs"]
        return words_to_value(self.interface.read(addrs))