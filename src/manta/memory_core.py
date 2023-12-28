from amaranth import *
from warnings import warn
from .utils import *
from math import ceil


class ReadOnlyMemoryCore(Elaboratable):
    def __init__(self, config, base_addr, interface):
        self.config = config
        self.base_addr = base_addr
        self.interface = interface

        self.check_config(config)

        self.depth = self.config["depth"]
        self.width = self.config["width"]
        self.max_addr = self.base_addr + (self.depth * ceil(self.width / 16))

        self.define_signals()
        self.define_mems()

    def check_config(self, config):
        # Check for unrecognized options
        valid_options = ["type", "depth", "width"]
        for option in config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in memory core.")

        # Check depth is provided and positive
        if "depth" not in config:
            raise ValueError("Depth of memory core must be specified.")

        if not isinstance(config["depth"], int):
            raise ValueError("Depth of memory core must be an integer.")

        if config["depth"] <= 0:
            raise ValueError("Depth of memory core must be positive. ")

        # Check width is provided and positive
        if "width" not in config:
            raise ValueError("Width of memory core must be specified.")

        if not isinstance(config["width"], int):
            raise ValueError("Width of memory core must be an integer.")

        if config["width"] <= 0:
            raise ValueError("Width of memory core must be positive. ")

    def define_signals(self):
        # Bus Input
        self.addr_i = Signal(16)
        self.data_i = Signal(16)
        self.rw_i = Signal(1)
        self.valid_i = Signal(1)

        # Bus Pipelining
        self.addr_pipe = [Signal(16) for _ in range(3)]
        self.data_pipe = [Signal(16) for _ in range(3)]
        self.rw_pipe = [Signal(1) for _ in range(3)]
        self.valid_pipe = [Signal(1) for _ in range(3)]

        # Bus Output
        self.addr_o = Signal(16, reset=0)
        self.data_o = Signal(16, reset=0)
        self.rw_o = Signal(1, reset=0)
        self.valid_o = Signal(1, reset=0)

        # User Port
        self.user_addr = Signal(range(self.depth))
        self.user_data = Signal(self.width)
        self.user_we = Signal(1)

    def pipeline_bus(self, m):
        # Pipelining
        m.d.sync += self.addr_pipe[0].eq(self.addr_i)
        m.d.sync += self.data_pipe[0].eq(self.data_i)
        m.d.sync += self.rw_pipe[0].eq(self.rw_i)
        m.d.sync += self.valid_pipe[0].eq(self.valid_i)

        for i in range(1, 3):
            m.d.sync += self.addr_pipe[i].eq(self.addr_pipe[i - 1])
            m.d.sync += self.data_pipe[i].eq(self.data_pipe[i - 1])
            m.d.sync += self.rw_pipe[i].eq(self.rw_pipe[i - 1])
            m.d.sync += self.valid_pipe[i].eq(self.valid_pipe[i - 1])

        m.d.sync += self.addr_o.eq(self.addr_pipe[2])
        m.d.sync += self.data_o.eq(self.data_pipe[2])
        m.d.sync += self.rw_o.eq(self.rw_pipe[2])
        m.d.sync += self.valid_o.eq(self.valid_pipe[2])

    def define_mems(self):
        # ok there's three cases:
        # 1. integer number of 16 bit mems
        # 2. integer number of 16 bit mems + partial mem
        # 3. just the partial mem (width < 16)

        # Only one, partial-width memory is needed
        if self.width < 16:
            self.mems = [Memory(depth=self.depth, width=self.width)]

        # Only full-width memories are needed
        elif self.width % 16 == 0:
            self.mems = [
                Memory(depth=self.depth, width=16) for _ in range(self.width // 16)
            ]

        # Both full-width and partial memories are needed
        else:
            self.mems = [
                Memory(depth=self.depth, width=16) for i in range(self.width // 16)
            ]
            self.mems += [Memory(depth=self.depth, width=self.width % 16)]

    def handle_read_ports(self, m):
        # These are tied to the bus
        for i, mem in enumerate(self.mems):
            read_port = mem.read_port()
            m.d.comb += read_port.en.eq(1)

            start_addr = self.base_addr + (i * self.depth)
            stop_addr = start_addr + self.depth - 1

            # Throw BRAM operations into the front of the pipeline
            with m.If(
                (self.valid_i)
                & (~self.rw_i)
                & (self.addr_i >= start_addr)
                & (self.addr_i <= stop_addr)
            ):
                m.d.sync += read_port.addr.eq(self.addr_i - start_addr)

            # Pull BRAM reads from the back of the pipeline
            with m.If(
                (self.valid_pipe[2])
                & (~self.rw_pipe[2])
                & (self.addr_pipe[2] >= start_addr)
                & (self.addr_pipe[2] <= stop_addr)
            ):
                m.d.sync += self.data_o.eq(read_port.data)

    def handle_write_ports(self, m):
        # These are given to the user
        for i, mem in enumerate(self.mems):
            write_port = mem.write_port()

            m.d.comb += write_port.addr.eq(self.user_addr)
            m.d.comb += write_port.data.eq(self.user_data[16 * i : 16 * (i + 1)])
            m.d.comb += write_port.en.eq(self.user_we)

    def elaborate(self, platform):
        m = Module()

        # Add memories as submodules
        for i, mem in enumerate(self.mems):
            m.submodules[f"mem_{i}"] = mem

        self.pipeline_bus(m)
        self.handle_read_ports(m)
        self.handle_write_ports(m)
        return m

    def get_top_level_ports(self):
        return [self.user_addr, self.user_data, self.user_we]

    def get_max_addr(self):
        return self.max_addr

    def read_from_user_addr(self, addrs):
        """
        Read the memory stored at the provided address, as seen from the user side.
        """

        # Convert user address space to bus address space
        # (for instance, for a core with base address 10 and width 33,
        # reading from address 4 is actually a read from address 14 and address 14 + depth, and address 14 + 2*depth)

        if isinstance(addrs, int):
            return self.read_from_user_addr([addrs])[0]

        bus_addrs = []
        for addr in addrs:
            bus_addrs += [
                addr + self.base_addr + i * self.depth for i in range(len(self.mems))
            ]

        datas = self.interface.read(bus_addrs)
        data_chunks = split_into_chunks(datas, len(self.mems))
        return [words_to_value(chunk) for chunk in data_chunks]

    # def write_to_user_addr(self, addrs, datas):
    #     """
    #     Read from the address
    #     """

    #     bus_addrs = []
    #     for addr in addrs:
    #         bus_addrs += [
    #             addr + self.base_addr + i * self.depth for i in range(len(self.mems))
    #         ]

    #     bus_datas = []
    #     for data in datas:
    #         bus_datas += value_to_words(data)

    #     self.interface.write(bus_addrs, bus_datas)
