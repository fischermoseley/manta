from amaranth import *

from manta.utils import *


class UDPSourceBridge(Elaboratable):
    """
    A module for bridging the AXI-stream of incoming UDP packet data to Manta's
    internal bus. Connects to the LiteEth core's "source" port.
    """

    def __init__(self):
        self.bus_o = Signal(InternalBus())

        self.data_i = Signal(32)
        self.last_i = Signal()
        self.ready_o = Signal()
        self.valid_i = Signal()

    def elaborate(self, platform):
        m = Module()

        state = Signal()  # Can either be 0, for read/write, or 1, for data
        rw_buf = Signal().like(self.bus_o.rw)

        # Can always take more data
        m.d.sync += self.ready_o.eq(1)

        m.d.sync += self.bus_o.eq(0)
        with m.If(self.valid_i):
            m.d.sync += state.eq(~state)

            with m.If(state == 0):
                m.d.sync += rw_buf.eq(self.data_i)

            with m.Else():
                m.d.sync += self.bus_o.addr.eq(self.data_i[:16])
                m.d.sync += self.bus_o.data.eq(self.data_i[16:])
                m.d.sync += self.bus_o.rw.eq(rw_buf)
                m.d.sync += self.bus_o.valid.eq(1)
                m.d.sync += self.bus_o.last.eq(self.last_i)

        return m
