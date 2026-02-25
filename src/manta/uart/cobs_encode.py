from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.fifo import SyncFIFO
from amaranth.lib.memory import Memory
from amaranth.lib.wiring import In, Out

from manta.utils import *


class COBSEncode(wiring.Component):
    sink: In(StreamSignature(8))
    source: Out(StreamSignature(8))

    def elaborate(self, platform):
        m = Module()

        m.submodules.fifo = fifo = SyncFIFO(width=8, depth=256)

        fsm_data = Signal(8)
        was_last = Signal(1)
        was_zero = Signal(1)
        fifo_written_to_last_cycle = Signal(1)
        m.d.comb += fifo_written_to_last_cycle.eq(
            (self.sink.ready) & (self.sink.valid) & (self.sink.data != 0)
        )

        with m.FSM() as fsm:
            with m.State("COUNT_BYTES"):
                with m.If(self.sink.valid & self.sink.ready):
                    # Send the length byte, as either a zero has been found, the end of the packet
                    # has been reached, or 254 bytes have been read in.
                    with m.If((self.sink.last) | (self.sink.data == 0) | (fifo.r_level == 253)):
                        # Handle edge case where 254th byte is a zero
                        with m.If(fifo.r_level == 253):
                            with m.If(self.sink.data == 0):
                                m.d.sync += fsm_data.eq(254)

                            with m.Else():
                                m.d.sync += fsm_data.eq(255)

                        with m.Else():
                            m.d.sync += fsm_data.eq(fifo.r_level + fifo_written_to_last_cycle + 1)

                        m.d.sync += was_last.eq(self.sink.last)
                        m.d.sync += was_zero.eq(self.sink.data == 0)
                        m.next = "SEND_LENGTH"

            with m.State("SEND_LENGTH"):
                with m.If(self.source.valid & self.source.ready):
                    m.next = "SEND_BYTES"

            with m.State("SEND_BYTES"):
                # Wait until the FIFO will be empty on next cycle
                with m.If(
                    ((fifo.r_level == 1) & (self.source.ready) & (self.source.valid))
                    | (fifo.r_level == 0)
                ):
                    m.next = "COUNT_BYTES"

                    with m.If(was_last):
                        with m.If(was_zero):
                            m.d.sync += fsm_data.eq(1)
                            m.next = "SEND_ONE"

                        with m.Else():
                            m.d.sync += fsm_data.eq(0)
                            m.next = "SEND_DELIMITER"

            with m.State("SEND_ONE"):
                with m.If(self.source.valid & self.source.ready):
                    m.d.sync += fsm_data.eq(0)
                    m.next = "SEND_DELIMITER"

            with m.State("SEND_DELIMITER"):
                with m.If(self.source.valid & self.source.ready):
                    m.next = "COUNT_BYTES"

        # Wire FIFO input to sink
        m.d.comb += fifo.w_data.eq(self.sink.data)
        m.d.comb += fifo.w_en.eq((self.sink.ready) & (self.sink.valid) & (self.sink.data != 0))
        m.d.comb += self.sink.ready.eq(fifo.w_rdy & fsm.ongoing("COUNT_BYTES"))

        # Wire FIFO output to source, allow FSM to preempt FIFO
        with m.If(
            fsm.ongoing("SEND_LENGTH") | fsm.ongoing("SEND_ONE") | fsm.ongoing("SEND_DELIMITER")
        ):
            m.d.comb += self.source.data.eq(fsm_data)
            m.d.comb += self.source.valid.eq(1)
            m.d.comb += fifo.r_en.eq(0)

        with m.Else():
            m.d.comb += self.source.data.eq(fifo.r_data)
            m.d.comb += self.source.valid.eq(fifo.r_rdy & fsm.ongoing("SEND_BYTES"))
            m.d.comb += fifo.r_en.eq(self.source.valid & self.source.ready)

        m.d.comb += self.source.last.eq(fsm.ongoing("SEND_DELIMITER"))

        return m
