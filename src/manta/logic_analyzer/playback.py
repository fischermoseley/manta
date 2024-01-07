from amaranth import *


class LogicAnalyzerPlayback(Elaboratable):
    """A synthesizable module that plays back data captured by a LogicAnalyzerCore.

    Parameters:
    ----------
    data : list[int]
        The raw captured data taken by the LogicAnalyzerCore. This consists of the values of
        all the input probes concatenated together at every timestep.

    config : dict
        The configuration of the LogicAnalyzerCore that took this capture.
    """
    def __init__(self, data, config):
        self.data = data
        self.config = config

        # State Machine
        self.start = Signal(1)
        self.valid = Signal(1)

        # Top-Level Probe signals
        self.top_level_probes = {}
        for name, width in self.config["probes"].items():
            self.top_level_probes[name] = Signal(width, name=name)

        # Instantiate memory
        self.mem = Memory(
            depth=self.config["sample_depth"],
            width=sum(self.config["probes"].values()),
            init=self.data,
        )

        self.read_port = self.mem.read_port()

    def elaborate(self, platform):
        m = Module()
        m.submodules["mem"] = self.mem

        m.d.comb += self.read_port.en.eq(1)

        # State Machine
        busy = Signal(1)
        with m.If(~busy):
            with m.If(self.start):
                m.d.sync += busy.eq(1)
                # m.d.sync += self.read_port.addr.eq(1)

        with m.Else():
            with m.If(self.read_port.addr == self.config["sample_depth"] - 1):
                m.d.sync += busy.eq(0)
                m.d.sync += self.read_port.addr.eq(0)

            with m.Else():
                m.d.sync += self.read_port.addr.eq(self.read_port.addr + 1)

        # Pipeline to accomodate for the 2-cycle latency in the RAM
        m.d.sync += self.valid.eq(busy)

        # Assign the probe values by part-selecting from the data port
        lower = 0
        for name, width in reversed(self.config["probes"].items()):
            signal = self.top_level_probes[name]

            # Set output probe to zero if we're not
            with m.If(self.valid):
                m.d.comb += signal.eq(self.read_port.data[lower : lower + width])

            with m.Else():
                m.d.comb += signal.eq(0)

            lower += width

        return m

    def get_top_level_ports(self):
        return [self.start, self.valid] + list(self.top_level_probes.values())
