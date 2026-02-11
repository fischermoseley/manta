from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class COBSDecode(wiring.Component):
    sink: In(StreamSignature(8, has_last=False, has_ready=False))
    source: Out(StreamSignature(8))

    def elaborate(self, platform):
        m = Module()

        counter = Signal(8)

        m.d.sync += self.source.data.eq(0)
        m.d.sync += self.source.valid.eq(0)
        m.d.sync += self.source.last.eq(0)

        # State Machine:
        with m.FSM():
            # TODO: determine if wait for packet logic should stay
            # with m.State("WAIT_FOR_PACKET_START"):
            #     with m.If((self.sink.data == 0) & (self.sink.valid)):
            #         m.next = "START_OF_PACKET"

            with m.State("START_OF_PACKET"):
                with m.If(self.sink.valid):
                    m.d.sync += counter.eq(self.sink.data - 1)
                    m.next = "DECODING"

                # with m.Else():
                #     m.next = "START_OF_PACKET"

            with m.State("DECODING"):
                with m.If(self.sink.valid):
                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                        m.d.sync += self.source.data.eq(self.sink.data)
                        m.d.sync += self.source.valid.eq(1)
                        m.next = "DECODING"

                    with m.Else():
                        with m.If(self.sink.data == 0):
                            m.d.sync += self.source.last.eq(1)
                            m.next = "START_OF_PACKET"

                        with m.Else():
                            m.d.sync += counter.eq(self.sink.data - 1)
                            m.d.sync += self.source.valid.eq(1)
                            m.next = "DECODING"

        return m
