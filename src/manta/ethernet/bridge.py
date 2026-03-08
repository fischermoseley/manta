from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class EthernetBridge(wiring.Component):
    source: Out(StreamSignature(32))
    sink: In(StreamSignature(32))

    bus_source: Out(InternalBusSignature)
    bus_sink: In(InternalBusSignature)

    def elaborate(self, platform):
        m = Module()

        msg_type = Signal(MessageTypes)
        seq_num_expected = Signal(13)

        seen_last = Signal()

        count = Signal(7)

        with m.FSM() as fsm:
            with m.State("IDLE"):
                with m.If(self.sink.valid & self.sink.ready):
                    # Send NACK if message type or sequence number is incorrect
                    with m.If(
                        (
                            (self.sink.data[:3] != MessageTypes.READ_REQUEST)
                            & (self.sink.data[:3] != MessageTypes.WRITE_REQUEST)
                        )
                        | (self.sink.data[3:16] != seq_num_expected)
                    ):
                        m.d.sync += seen_last.eq(self.sink.last)
                        m.next = "NACK"

                    with m.Else():
                        m.d.sync += msg_type.eq(self.sink.data[:3])
                        m.d.sync += count.eq(self.sink.data[16:23])
                        m.next = "WAIT_FOR_ADDR"

            with m.State("WAIT_FOR_ADDR"):
                with m.If(self.sink.valid & self.sink.ready):
                    m.d.sync += self.bus_source.p.addr.eq(self.sink.data)
                    m.d.sync += seq_num_expected.eq(seq_num_expected + 1)

                    with m.If(msg_type == MessageTypes.READ_REQUEST):
                        # Send read response header
                        m.d.sync += self.source.valid.eq(1)
                        m.d.sync += self.source.last.eq(0)
                        m.d.sync += self.source.data.eq(
                            EthernetMessageHeader.concat_signals(
                                MessageTypes.READ_RESPONSE,
                                seq_num_expected,
                            )
                        )

                        m.next = "READ"

                    with m.Elif(msg_type == MessageTypes.WRITE_REQUEST):
                        m.next = "WRITE"

            with m.State("WRITE"):
                # Keep a running count of the number of requests inflight on the bus
                # Once that hits zero and seen_last is high, we're done!
                # Send write response and wait for it to clock out

                m.d.sync += seen_last.eq(
                    seen_last | (self.sink.last & self.sink.valid & self.sink.ready)
                )
                m.d.sync += count.eq(
                    count + (self.sink.valid & self.sink.ready) - self.bus_sink.p.valid
                )

                with m.If(self.sink.valid & self.sink.ready):
                    m.d.sync += self.bus_source.p.addr.eq(self.bus_source.p.addr + 1)
                    m.d.sync += self.bus_source.p.data.eq(self.sink.data)
                    m.d.sync += self.bus_source.p.rw.eq(1)
                    m.d.sync += self.bus_source.p.valid.eq(1)

                with m.Else():
                    m.d.sync += self.bus_source.p.data.eq(0)  # just for clarity of debugging
                    m.d.sync += self.bus_source.p.rw.eq(0)  # just for clarity of debugging
                    m.d.sync += self.bus_source.p.valid.eq(0)

                with m.If(seen_last & (count == 0)):
                    with m.If(self.source.valid & self.source.ready):
                        m.d.sync += self.source.valid.eq(0)
                        m.d.sync += self.source.last.eq(0)  # just for clarity of debugging
                        m.d.sync += self.source.data.eq(0)  # just for clarity of debugging
                        m.next = "IDLE"

                    with m.Else():
                        m.d.sync += self.source.valid.eq(1)
                        m.d.sync += self.source.last.eq(1)
                        m.d.sync += self.source.data.eq(
                            EthernetMessageHeader.concat_signals(
                                MessageTypes.WRITE_RESPONSE,
                                seq_num_expected,
                            )
                        )

            with m.State("READ"):
                # Wait for downstream to accept data. Put next read request on the bus after it's accepted, if more is needed
                m.d.sync += self.bus_source.p.valid.eq(0)
                with m.If(self.source.valid):
                    with m.If(self.source.ready):
                        m.d.sync += self.source.valid.eq(0)
                        m.d.sync += self.source.data.eq(0)  # for debugging
                        m.d.sync += self.source.last.eq(0)  # for debugging

                        with m.If(self.source.last):
                            m.next = "IDLE"

                        with m.Else():
                            m.d.sync += self.bus_source.p.rw.eq(0)
                            m.d.sync += self.bus_source.p.valid.eq(1)
                            m.d.sync += count.eq(count - 1)

                # Not waiting on downstream to accept data. No need to issue bus request.
                # Instead check if data's available on bus_sink, and put it on source if so
                with m.Else():
                    with m.If(self.bus_sink.p.valid):
                        m.d.sync += self.source.data.eq(self.bus_sink.p.data)
                        m.d.sync += self.source.valid.eq(1)
                        m.d.sync += self.source.last.eq(count == 0)
                        m.d.sync += self.bus_source.p.addr.eq(self.bus_source.p.addr + 1)

            with m.State("NACK"):
                # Only send NACK after full packet has been received
                with m.If(seen_last | (self.sink.valid & self.sink.ready & self.sink.last)):
                    m.d.sync += self.source.valid.eq(1)
                    m.d.sync += self.source.last.eq(1)
                    m.d.sync += self.source.data.eq(
                        EthernetMessageHeader.concat_signals(
                            MessageTypes.NACK,
                            seq_num_expected,
                        )
                    )

                with m.If(self.source.valid & self.source.ready):
                    m.next = "IDLE"

                    m.d.sync += self.source.valid.eq(0)
                    m.d.sync += self.source.last.eq(0)
                    m.d.sync += self.source.data.eq(0)

        m.d.comb += self.sink.ready.eq(~fsm.ongoing("READ"))

        return m
