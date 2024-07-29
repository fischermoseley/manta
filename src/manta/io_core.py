from amaranth import *
from manta.utils import *
from math import ceil


class IOCore(MantaCore):
    """
    A module for setting and getting the values of registers of arbitrary size
    on a FPGA.

    Provides methods for generating synthesizable logic for the FPGA, as well
    as methods for reading and writing the value of a register.

    More information available in the online documentation at:
    https://fischermoseley.github.io/manta/io_core/
    """

    def __init__(self, inputs=[], outputs=[]):
        self._inputs = inputs
        self._outputs = outputs

        # Bus Connections
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        # Internal Signals
        self._strobe = Signal()
        self._input_bufs = [Signal(len(p), name=p.name + "_buf") for p in self._inputs]
        self._output_bufs = [
            Signal(len(p), name=p.name + "_buf", init=p.init) for p in self._outputs
        ]

    @property
    def top_level_ports(self):
        return self._inputs + self._outputs

    @property
    def max_addr(self):
        self._make_memory_map()
        return self._max_addr

    @classmethod
    def from_config(cls, config, base_addr, interface):
        inputs = config.get("inputs", {})
        outputs = config.get("outputs", {})

        # Make sure IO core has at least one input or output
        if not inputs and not outputs:
            raise ValueError("Must specify at least one input or output port.")

        # Warn about unrecognized options
        valid_options = ["type", "inputs", "outputs"]
        for option in config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in IO core.'")

        # Define input signals
        input_signals = []
        for name, width in inputs.items():
            if not isinstance(name, str):
                raise ValueError(
                    f'Input probe "{name}" has invalid name, names must be strings.'
                )

            if not isinstance(width, int):
                raise ValueError(f"Input probe '{name}' must have integer width.")

            if not width > 0:
                raise ValueError(f"Input probe '{name}' must have positive width.")

            input_signals += [Signal(width, name=name)]

        # Define output signals
        output_signals = []
        for name, attrs in outputs.items():
            if not isinstance(name, str):
                raise ValueError(
                    f'Output probe "{name}" has invalid name, names must be strings.'
                )

            if not isinstance(attrs, int) and not isinstance(attrs, dict):
                raise ValueError(f'Unrecognized format for output probe "{name}".')

            if isinstance(attrs, int):
                if not attrs > 0:
                    raise ValueError(f'Output probe "{name}" must have positive width.')

                width = attrs
                initial_value = 0

            if isinstance(attrs, dict):
                # Check that each output probe has only recognized options
                valid_options = ["width", "initial_value"]
                for option in attrs:
                    if option not in valid_options:
                        warn(f'Ignoring unrecognized option "{option}" in IO core.')

                # Check that widths are appropriate
                if "width" not in attrs:
                    raise ValueError(f"No width specified for output probe {name}.")

                if not isinstance(attrs["width"], int):
                    raise ValueError(f'Output probe "{name}" must have integer width.')

                if not attrs["width"] > 0:
                    raise ValueError(f'Input probe "{name}" must have positive width.')

                width = attrs["width"]

                initial_value = 0
                if "initial_value" in attrs:
                    if not isinstance(attrs["initial_value"], int):
                        raise ValueError("Initial value must be an integer.")

                    check_value_fits_in_bits(attrs["initial_value"], width)
                    initial_value = attrs["initial_value"]

            output_signals += [Signal(width, name=name, init=initial_value)]

        return cls(base_addr, interface, inputs=input_signals, outputs=output_signals)

    def to_config(self):
        config = {}
        config["type"] = "io"

        if self._inputs:
            config["inputs"] = {s.name: len(s) for s in self._inputs}

        if self._outputs:
            config["outputs"] = {}
            for s in self._outputs:
                config["outputs"][s.name] = {"width": len(s), "initial_value": s.init}

        return config

    def _make_memory_map(self):
        self._memory_map = {}

        # Add strobe register
        self._memory_map["strobe"] = dict(
            signals=[self._strobe], addrs=[self.base_addr]
        )

        # Assign memory to all inputs and outputs
        ios = self._inputs + self._outputs
        io_bufs = self._input_bufs + self._output_bufs
        last_used_addr = self.base_addr

        for io, io_buf in zip(ios, io_bufs):
            n_slices = ceil(len(io) / 16)
            signals = split_into_chunks(io_buf, 16)
            addrs = [i + last_used_addr + 1 for i in range(n_slices)]

            self._memory_map[io.name] = dict(signals=signals, addrs=addrs)

            last_used_addr = addrs[-1]

        # Save the last used address, for use later.
        # Normally we'd just grab this from self._memory_map, but Python
        # dictionaries don't guaruntee that insertion order is preserved,
        # so it's more convenient to just save it now.

        self._max_addr = last_used_addr

    def elaborate(self, platform):
        m = Module()

        # Shuffle bus transactions along
        m.d.sync += self.bus_o.eq(self.bus_i)

        # Update input_buffers from inputs
        for i, i_buf in zip(self._inputs, self._input_bufs):
            with m.If(self._strobe):
                m.d.sync += i_buf.eq(i)

        # Update outputs from output_buffers
        for o, o_buf in zip(self._outputs, self._output_bufs):
            with m.If(self._strobe):
                m.d.sync += o.eq(o_buf)

        # Handle register reads and writes
        for io in self._memory_map.values():
            for addr, signal in zip(io["addrs"], io["signals"]):
                with m.If(self.bus_i.addr == addr):
                    # Writes
                    with m.If(self.bus_i.rw):
                        m.d.sync += signal.eq(self.bus_i.data)

                    # Reads
                    with m.Else():
                        m.d.sync += self.bus_o.data.eq(signal)

        return m

    def set_probe(self, name, value):
        """
        Set the value of an output probe on the FPGA. The value may be either
        an unsigned or signed integer, but must fit within the width of the
        probe.
        """

        # Check that probe exists in memory map
        probe = self._memory_map.get(name)
        if not probe:
            raise KeyError(f"Probe '{name}' not found in IO core.")

        # Check that the probe is an output
        if not any([o.name == name for o in self._outputs]):
            raise KeyError(f"Probe '{name}' is not an output of the IO core.")

        # Check that value isn't too big for the register
        n_bits = sum([len(s) for s in probe["signals"]])
        check_value_fits_in_bits(value, n_bits)

        # Write value to core
        addrs = probe["addrs"]
        datas = value_to_words(value, len(addrs))
        self.interface.write(addrs, datas)

        # Pulse strobe register
        self.interface.write(self.base_addr, 0)
        self.interface.write(self.base_addr, 1)
        self.interface.write(self.base_addr, 0)

    def get_probe(self, name):
        """
        Get the present value of a probe on the FPGA, which is returned as an
        unsigned integer. This function may be called on both input and output
        probes, but output probes will return the last value written to them
        (or their initial value, if no value has been written to them yet).
        """

        # Check that probe exists in memory map
        probe = self._memory_map.get(name)
        if not probe:
            raise KeyError(f"Probe with name {name} not found in IO core.")

        # Pulse strobe register
        self.interface.write(self.base_addr, 0)
        self.interface.write(self.base_addr, 1)
        self.interface.write(self.base_addr, 0)

        # Get value from buffer
        datas = self.interface.read(probe["addrs"])
        return words_to_value(datas)
