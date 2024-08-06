from amaranth import *

from manta.utils import *


class UDPSinkBridge(Elaboratable):
    """
    A module for bridging Manta's internal bus to an AXI stream of UDP packet
    data. Connects to the LiteEth core's "sink" port.
    """

    def __init__(self):
        self.bus_i = Signal(InternalBus())

        self.data_o = Signal(32)
        self.last_o = Signal()
        self.ready_i = Signal()
        self.valid_o = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.sync += self.data_o.eq(0)
        m.d.sync += self.last_o.eq(0)
        m.d.sync += self.valid_o.eq(0)

        with m.If((self.bus_i.valid) & (~self.bus_i.rw)):
            m.d.sync += self.data_o.eq(self.bus_i.data)
            m.d.sync += self.last_o.eq(self.bus_i.last)
            m.d.sync += self.valid_o.eq(1)

        return m
