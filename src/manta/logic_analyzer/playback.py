from amaranth import *


class LogicAnalyzerPlayback(Elaboratable):
    """
    A synthesizable module that plays back data captured by a
    LogicAnalyzerCore. Takes a list of all the samples captured by a core,
    along with the config of the core used to take it.
    """

    def __init__(self, probes, data):
        self._probes = probes
        self._data = data

        # State Machine
        self.start = Signal(1)
        self.valid = Signal(1)

    def elaborate(self, platform):
        m = Module()

        # Instantiate memory
        self.mem = Memory(
            depth=len(self._data),
            width=sum([len(p) for p in self._probes]),
            init=self._data,
        )
        m.submodules.mem = self.mem

        read_port = self.mem.read_port()

        m.d.comb += read_port.en.eq(1)

        # State Machine
        busy = Signal(1)
        with m.If(~busy):
            with m.If(self.start):
                m.d.sync += busy.eq(1)
                # m.d.sync += read_port.addr.eq(1)

        with m.Else():
            with m.If(read_port.addr == len(self._data) - 1):
                m.d.sync += busy.eq(0)
                m.d.sync += read_port.addr.eq(0)

            with m.Else():
                m.d.sync += read_port.addr.eq(read_port.addr + 1)

        # Pipeline to accommodate for the 2-cycle latency in the RAM
        m.d.sync += self.valid.eq(busy)

        # Assign the probe values by part-selecting from the data port
        lower = 0
        for p in reversed(self._probes):
            # Set output probe to zero if we're not
            with m.If(self.valid):
                m.d.comb += p.eq(read_port.data[lower : lower + len(p)])

            with m.Else():
                m.d.comb += p.eq(0)

            lower += len(p)

        return m

    def get_top_level_ports(self):
        """
        Returns the Amaranth signals that should be included as ports in the
        exported Verilog module.
        """
        return [self.start, self.valid] + self._probes
