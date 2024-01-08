from amaranth import *


class TransmitBridge(Elaboratable):
    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(16)
        self.rw_i = Signal()
        self.valid_i = Signal()

        self.data_o = Signal(8, reset=0)
        self.start_o = Signal(1)
        self.done_i = Signal()

        # Internal Signals
        self.buffer = Signal(16, reset=0)
        self.count = Signal(4, reset=0)
        self.busy = Signal(1, reset=0)
        self.to_ascii_hex = Signal(8)
        self.n = Signal(4)

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.start_o.eq(self.busy)

        with m.If(~self.busy):
            with m.If((self.valid_i) & (~self.rw_i)):
                m.d.sync += self.busy.eq(1)
                m.d.sync += self.buffer.eq(self.data_i)

        with m.Else():
            # uart_tx is transmitting a byte:
            with m.If(self.done_i):
                m.d.sync += self.count.eq(self.count + 1)

                # Message has been transmitted
                with m.If(self.count > 5):
                    m.d.sync += self.count.eq(0)

                    # Go back to idle, or transmit next message
                    with m.If((self.valid_i) & (~self.rw_i)):
                        m.d.sync += self.buffer.eq(self.data_i)

                    with m.Else():
                        m.d.sync += self.busy.eq(0)

        # define to_ascii_hex
        with m.If(self.n < 10):
            m.d.comb += self.to_ascii_hex.eq(self.n + 0x30)
        with m.Else():
            m.d.comb += self.to_ascii_hex.eq(self.n + 0x41 - 10)

        # run the sequence
        with m.If(self.count == 0):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("D"))

        with m.Elif(self.count == 1):
            m.d.comb += self.n.eq(self.buffer[12:16])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 2):
            m.d.comb += self.n.eq(self.buffer[8:12])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 3):
            m.d.comb += self.n.eq(self.buffer[4:8])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 4):
            m.d.comb += self.n.eq(self.buffer[0:4])
            m.d.comb += self.data_o.eq(self.to_ascii_hex)

        with m.Elif(self.count == 5):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("\r"))

        with m.Elif(self.count == 6):
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(ord("\n"))

        with m.Else():
            m.d.comb += self.n.eq(0)
            m.d.comb += self.data_o.eq(0)

        return m
