from math import ceil

from amaranth import *
from amaranth.lib.memory import Memory

from manta.utils import *


class MemoryCore(MantaCore):
    """
    A synthesizable module for accessing a memory. This is accomplished by
    instantiating a dual-port memory with one end tied to Manta's internal bus,
    and the other provided to user logic.
    """

    def __init__(self, mode, width, depth):
        """
        Create a Memory Core with the given width and depth.

        This function is the main mechanism for configuring a Memory Core in an
        Amaranth-native design.

        Args:
            mode (str): Must be one of `bidirectional`, `host_to_fpga`, or
                'fpga_to_host'. Bidirectional memories can be both read or
                written to by the host and FPGA, but they require the use
                of a True Dual Port RAM, which is not available on all
                platforms (most notably, the ice40). Host-to-fpga and
                fpga-to-host RAMs only require a Simple Dual Port RAM, which
                is available on nearly all platforms.

            width (int): The width of the memory, in bits.

            depth (int): The depth of the memory, in entries.
        """
        self._mode = mode
        self._width = width
        self._depth = depth

        self._n_mems = ceil(self._width / 16)

        # Bus Connections
        self.bus_i = Signal(InternalBus())
        self.bus_o = Signal(InternalBus())

        # User Ports
        if self._mode == "fpga_to_host":
            self.user_addr = Signal(range(self._depth))
            self.user_data_in = Signal(self._width)
            self.user_write_enable = Signal()
            self._top_level_ports = [
                self.user_addr,
                self.user_data_in,
                self.user_write_enable,
            ]

        elif self._mode == "host_to_fpga":
            self.user_addr = Signal(range(self._depth))
            self.user_data_out = Signal(self._width)
            self._top_level_ports = [
                self.user_addr,
                self.user_data_out,
            ]

        elif self._mode == "bidirectional":
            self.user_addr = Signal(range(self._depth))
            self.user_data_in = Signal(self._width)
            self.user_data_out = Signal(self._width)
            self.user_write_enable = Signal()
            self._top_level_ports = [
                self.user_addr,
                self.user_data_in,
                self.user_data_out,
                self.user_write_enable,
            ]

        # Define memories
        n_full = self._width // 16
        n_partial = self._width % 16

        self._mems = [
            Memory(shape=16, depth=self._depth, init=[0] * self._depth)
            for _ in range(n_full)
        ]
        if n_partial > 0:
            self._mems += [
                Memory(shape=n_partial, depth=self._depth, init=[0] * self._depth)
            ]

    @property
    def top_level_ports(self):
        return self._top_level_ports

    @property
    def max_addr(self):
        return self.base_addr + (self._depth * self._n_mems)

    def to_config(self):
        return {
            "type": "memory",
            "mode": self._mode,
            "width": self._width,
            "depth": self._depth,
        }

    @classmethod
    def from_config(cls, config):
        # Check for unrecognized options
        valid_options = ["type", "depth", "width", "mode"]
        for option in config:
            if option not in valid_options:
                warn(f"Ignoring unrecognized option '{option}' in memory core.")

        # Check depth is provided and positive
        depth = config.get("depth")
        if not depth:
            raise ValueError("Depth of memory core must be specified.")

        if not isinstance(depth, int):
            raise ValueError("Depth of memory core must be an integer.")

        if not depth > 0:
            raise ValueError("Depth of memory core must be positive. ")

        # Check width is provided and positive
        width = config.get("width")
        if not width:
            raise ValueError("Width of memory core must be specified.")

        if not isinstance(width, int):
            raise ValueError("Width of memory core must be an integer.")

        if not width > 0:
            raise ValueError("Width of memory core must be positive. ")

        # Check mode is provided and is recognized value
        mode = config.get("mode")
        if not mode:
            raise ValueError("Mode of memory core must be specified.")

        if mode not in ["fpga_to_host", "host_to_fpga", "bidirectional"]:
            raise ValueError("Unrecognized mode provided to memory core.")

        return cls(mode, width, depth)

    def _tie_mems_to_bus(self, m):
        for i, mem in enumerate(self._mems):
            # Compute address range corresponding to this chunk of memory
            start_addr = self.base_addr + (i * self._depth)
            stop_addr = start_addr + self._depth - 1

            if self._mode == "fpga_to_host":
                read_port = mem.read_port()
                m.d.comb += read_port.en.eq(1)

                # Throw BRAM operations into the front of the pipeline
                with m.If(
                    (self.bus_i.valid)
                    & (self.bus_i.addr >= start_addr)
                    & (self.bus_i.addr <= stop_addr)
                ):
                    m.d.sync += read_port.addr.eq(self.bus_i.addr - start_addr)

                # Pull BRAM reads from the back of the pipeline
                with m.If(
                    (self._bus_pipe[2].valid)
                    & (~self._bus_pipe[2].rw)
                    & (self._bus_pipe[2].addr >= start_addr)
                    & (self._bus_pipe[2].addr <= stop_addr)
                ):
                    m.d.sync += self.bus_o.data.eq(read_port.data)

            elif self._mode == "host_to_fpga":
                write_port = mem.write_port()
                m.d.sync += write_port.en.eq(0)

                # Throw BRAM operations into the front of the pipeline
                with m.If(
                    (self.bus_i.valid)
                    & (self.bus_i.addr >= start_addr)
                    & (self.bus_i.addr <= stop_addr)
                ):
                    m.d.sync += write_port.addr.eq(self.bus_i.addr - start_addr)
                    m.d.sync += write_port.data.eq(self.bus_i.data)
                    m.d.sync += write_port.en.eq(self.bus_i.rw)

            elif self._mode == "bidirectional":
                read_port = mem.read_port()
                m.d.comb += read_port.en.eq(1)

                write_port = mem.write_port()
                m.d.sync += write_port.en.eq(0)

                # Throw BRAM operations into the front of the pipeline
                with m.If(
                    (self.bus_i.valid)
                    & (self.bus_i.addr >= start_addr)
                    & (self.bus_i.addr <= stop_addr)
                ):
                    m.d.sync += read_port.addr.eq(self.bus_i.addr - start_addr)
                    m.d.sync += write_port.addr.eq(self.bus_i.addr - start_addr)
                    m.d.sync += write_port.data.eq(self.bus_i.data)
                    m.d.sync += write_port.en.eq(self.bus_i.rw)

                # Pull BRAM reads from the back of the pipeline
                with m.If(
                    (self._bus_pipe[2].valid)
                    & (~self._bus_pipe[2].rw)
                    & (self._bus_pipe[2].addr >= start_addr)
                    & (self._bus_pipe[2].addr <= stop_addr)
                ):
                    m.d.sync += self.bus_o.data.eq(read_port.data)

    def _tie_mems_to_user_logic(self, m):
        # Handle write ports
        if self._mode in ["fpga_to_host", "bidirectional"]:
            for i, mem in enumerate(self._mems):
                write_port = mem.write_port()
                m.d.comb += write_port.addr.eq(self.user_addr)
                m.d.comb += write_port.data.eq(self.user_data_in[16 * i : 16 * (i + 1)])
                m.d.comb += write_port.en.eq(self.user_write_enable)

        # Handle read ports
        if self._mode in ["host_to_fpga", "bidirectional"]:
            read_datas = []
            for i, mem in enumerate(self._mems):
                read_port = mem.read_port()
                m.d.comb += read_port.addr.eq(self.user_addr)
                m.d.comb += read_port.en.eq(1)
                read_datas.append(read_port.data)

            m.d.comb += self.user_data_out.eq(Cat(read_datas))

    def elaborate(self, platform):
        m = Module()

        # Add memories as submodules
        for i, mem in enumerate(self._mems):
            m.submodules[f"mem_{i}"] = mem

        # Pipeline the bus to accommodate the two clock-cycle delay in the memories
        self._bus_pipe = [Signal(InternalBus()) for _ in range(3)]
        m.d.sync += self._bus_pipe[0].eq(self.bus_i)

        for i in range(1, 3):
            m.d.sync += self._bus_pipe[i].eq(self._bus_pipe[i - 1])

        m.d.sync += self.bus_o.eq(self._bus_pipe[2])

        self._tie_mems_to_bus(m)
        self._tie_mems_to_user_logic(m)
        return m

    def _convert_user_to_bus_addr(self, addrs):
        """
        Convert user address space to bus address space. For instance, for a
        core with base address 10 and width 33, reading from address 4 is
        actually a read from address 14 and address 14 + depth, and address
        14 + (2 * depth).
        """
        if isinstance(addrs, int):
            return self._convert_user_to_bus_addr([addrs])[0]

        bus_addrs = []
        for addr in addrs:
            for i in range(len(self._mems)):
                bus_addrs.append(self.base_addr + addr + (i * self._depth))

        return bus_addrs

    def read(self, addrs):
        """
        Read the data stored in the Memory Core at one or many address.

        This function can read from either one or multiple addresses at a time.
        Due to the the IO latency in most OSes, a single multi-address read is
        significantly faster than multiple single-address reads. Prefer their
        usage where possible. This method is blocking.

        Args:
            addrs (int | List[int]): The memory address (or addresses) to read
                from.

        Returns:
            datas (int | List[int]): The data stored at the address (or
                addresses), represented as an unsigned integer.

        Raises:
            TypeError: addrs is not an integer or list of integers.

        """

        # Handle a single integer address
        if isinstance(addrs, int):
            return self.read([addrs])[0]

        # Make sure all list elements are integers
        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Read address must be an integer or list of integers.")

        bus_addrs = self._convert_user_to_bus_addr(addrs)
        datas = self.interface.read(bus_addrs)
        data_chunks = split_into_chunks(datas, self._n_mems)
        return [words_to_value(chunk) for chunk in data_chunks]

    def write(self, addrs, datas):
        """
        Write data to the Memory core at one or many addresses.

        This function can write to either one or multiple addresses at a time.
        Due to the the IO latency in most OSes, a single multi-address write is
        significantly faster than multiple single-address write. Prefer their
        usage where possible. This method is blocking.

        Args:
            addrs (int | List[int]): The memory address (or addresses) to write
                to.

            datas (int | List[int]): The data to store at the address (or
                addresses). This may be either positive or negative, but must
                fit within the width of the memory.

        Returns:
            None

        Raises:
            TypeError: addrs or datas is not an integer or list of integers.

        """

        # Handle a single integer address and data
        if isinstance(addrs, int) and isinstance(datas, int):
            return self.write([addrs], [datas])

        # Make sure address and datas are all integers
        if not isinstance(addrs, list) or not isinstance(datas, list):
            raise TypeError(
                "Write addresses and data must be an integer or list of integers."
            )

        if not all(isinstance(a, int) for a in addrs):
            raise TypeError("Write addresses must be all be integers.")

        if not all(isinstance(d, int) for d in datas):
            raise TypeError("Write data must all be integers.")

        bus_addrs = self._convert_user_to_bus_addr(addrs)
        bus_datas = [word for d in datas for word in value_to_words(d, self._n_mems)]
        self.interface.write(bus_addrs, bus_datas)
