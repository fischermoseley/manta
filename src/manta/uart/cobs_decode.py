from amaranth import *


class COBSDecode(Elaboratable):
    def __init__(self):
        # Stream-like data input
        self.data_i = Signal(8)
        self.valid_i = Signal()

        # Stream-like data output
        self.data_o = Signal(8)
        self.valid_o = Signal()
        self.last_o = Signal()

    def elaborate(self, platform):
        m = Module()

        counter = Signal(8)

        m.d.sync += self.data_o.eq(0)
        m.d.sync += self.valid_o.eq(0)
        m.d.sync += self.last_o.eq(0)

        # State Machine:
        with m.FSM():
            with m.State("WAIT_FOR_PACKET_START"):
                with m.If((self.data_i == 0) & (self.valid_i)):
                    m.next = "START_OF_PACKET"

            with m.State("START_OF_PACKET"):
                with m.If(self.valid_i):
                    m.d.sync += counter.eq(self.data_i - 1)
                    m.next = "DECODING"

                with m.Else():
                    m.next = "START_OF_PACKET"

            with m.State("DECODING"):
                with m.If(self.valid_i):
                    with m.If(counter > 0):
                        m.d.sync += counter.eq(counter - 1)
                        m.d.sync += self.data_o.eq(self.data_i)
                        m.d.sync += self.valid_o.eq(1)
                        m.next = "DECODING"

                    with m.Else():
                        with m.If(self.data_i == 0):
                            m.d.sync += self.last_o.eq(1)
                            m.next = "START_OF_PACKET"

                        with m.Else():
                            m.d.sync += counter.eq(self.data_i - 1)
                            m.d.sync += self.valid_o.eq(1)
                            m.next = "DECODING"

        return m
