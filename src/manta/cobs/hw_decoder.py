from amaranth import *
from amaranth.lib.memory import Memory

class COBSDecoder(Elaboratable):
    def __init__(self):

        # Stream-like data input
        self.data_in = Signal(8)
        self.data_in_valid = Signal(1)

        # Stream-like data output
        self.data_out = Signal(8)
        self.data_out_valid = Signal(1)
        self.end_of_packet = Signal(1)

    def elaborate(self, platform):
        m = Module()

        counter = Signal(8)

        m.d.sync += self.data_out.eq(0)
        m.d.sync += self.data_out_valid.eq(0)
        m.d.sync += self.end_of_packet.eq(0)

        # State Machine:
        with m.FSM() as fsm:
            with m.State("WAIT_FOR_PACKET_START"):
                with m.If( (self.data_in == 0) & (self.data_in_valid) ):
                    m.next = "START_OF_PACKET"

            with m.State("START_OF_PACKET"):
                with m.If(self.data_in_valid):
                    m.d.sync += counter.eq(self.data_in - 1)
                    m.next = "DECODING"

                with m.Else():
                    m.next = "START_OF_PACKET"

            with m.State("DECODING"):
                with m.If(self.data_in_valid):
                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                        m.d.sync += self.data_out.eq(self.data_in)
                        m.d.sync += self.data_out_valid.eq(1)
                        m.next = "DECODING"

                    with m.Else():
                        with m.If(self.data_in == 0):
                            m.d.sync += self.end_of_packet.eq(1)
                            m.next = "START_OF_PACKET"

                        with m.Else():
                            m.d.sync += counter.eq(self.data_in - 1)
                            m.d.sync += self.data_out_valid.eq(1)
                            m.next = "DECODING"

        return m