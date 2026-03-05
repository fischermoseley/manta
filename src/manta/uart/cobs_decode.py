from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.fifo import SyncFIFOBuffered
from amaranth.lib.wiring import In, Out

from manta.utils import *


class COBSDecode(wiring.Component):
    sink: In(StreamSignature(8, has_last=False))
    source: Out(StreamSignature(8))

    def elaborate(self, platform):
        m = Module()
        m.submodules.fifo = fifo = SyncFIFOBuffered(width=8, depth=3)

        count = Signal(range(256))
        fsm_inject_zero = Signal()
        skip_zero_injection = Signal()

        with m.FSM() as fsm:
            # m.d.comb += fsm_inject_zero.eq(0)

            with m.State("IDLE"):
                with m.If(self.sink.ready & self.sink.valid):
                    # Re-sync to start of packet
                    with m.If(self.sink.data != 0):
                        with m.If(self.sink.data == 1):
                            m.next = "END_OF_GROUP"

                        with m.Else():
                            m.next = "STREAM"
                            m.d.sync += count.eq(self.sink.data - 2)

                        m.d.sync += skip_zero_injection.eq(self.sink.data == 255)

            with m.State("STREAM"):
                with m.If(self.sink.ready & self.sink.valid):
                    with m.If(count > 0):
                        m.d.sync += count.eq(count - 1)

                    with m.Else():
                        m.next = "END_OF_GROUP"

            with m.State("END_OF_GROUP"):
                with m.If(self.sink.ready & self.sink.valid):
                    with m.If(self.sink.data == 0):
                        m.next = "IDLE"

                    with m.Elif(self.sink.data == 1):
                        # m.d.comb += fsm_inject_zero.eq(~skip_zero_injection)
                        m.next = "END_OF_GROUP"

                    with m.Else():
                        # m.d.comb += fsm_inject_zero.eq(~skip_zero_injection)
                        m.next = "STREAM"
                        m.d.sync += count.eq(self.sink.data - 2)

                    m.d.sync += skip_zero_injection.eq(self.sink.data == 255)

        # an attempt to fix the combo glitch on fsm_inject_zero
        m.d.comb += fsm_inject_zero.eq(
            fsm.ongoing("END_OF_GROUP")
            & self.sink.ready
            & self.sink.valid
            & (self.sink.data != 0)
            & (~skip_zero_injection)
        )

        m.d.comb += [
            self.source.data.eq(fifo.r_data),
            self.source.valid.eq(fifo.r_rdy & (fsm.ongoing("IDLE") | (fifo.r_level > 1))),
            self.source.last.eq(fsm.ongoing("IDLE") & self.source.valid & (fifo.r_level == 1)),
            fifo.r_en.eq(self.source.valid & self.source.ready),
        ]

        with m.If(fsm.ongoing("STREAM")):
            m.d.comb += [
                fifo.w_en.eq(self.sink.valid & self.sink.ready),
                fifo.w_data.eq(self.sink.data),
                self.sink.ready.eq(fifo.w_rdy),
            ]

        with m.Else():
            m.d.comb += [
                fifo.w_en.eq(fsm_inject_zero),
                fifo.w_data.eq(0),
                self.sink.ready.eq(
                    ~(
                        (fsm.ongoing("IDLE") & fifo.r_rdy)
                        | (fsm.ongoing("END_OF_GROUP") & ~fifo.w_rdy)
                    )
                ),
            ]

        return m
