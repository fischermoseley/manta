from amaranth import *


class UARTTransmitter(Elaboratable):
    def __init__(self, clocks_per_baud):
        self.clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.data_i = Signal(8)
        self.start_i = Signal()
        self.done_o = Signal(reset=1)

        self.tx = Signal(reset=1)

        # Internal Signals
        self.baud_counter = Signal(range(clocks_per_baud))
        self.buffer = Signal(9)
        self.bit_index = Signal(4)

    def elaborate(self, platform):
        m = Module()

        with m.If((self.start_i) & (self.done_o)):
            m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)
            m.d.sync += self.buffer.eq(Cat(self.data_i, 1))
            m.d.sync += self.bit_index.eq(0)
            m.d.sync += self.done_o.eq(0)
            m.d.sync += self.tx.eq(0)

        with m.Elif(~self.done_o):
            m.d.sync += self.baud_counter.eq(self.baud_counter - 1)
            m.d.sync += self.done_o.eq((self.baud_counter == 1) & (self.bit_index == 9))

            # A baud period has elapsed
            with m.If(self.baud_counter == 0):
                m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)

                # Clock out another bit if there are any left
                with m.If(self.bit_index < 9):
                    m.d.sync += self.tx.eq(self.buffer.bit_select(self.bit_index, 1))
                    m.d.sync += self.bit_index.eq(self.bit_index + 1)

                # Byte has been sent, send out next one or go to idle
                with m.Else():
                    with m.If(self.start_i):
                        m.d.sync += self.buffer.eq(Cat(self.data_i, 1))
                        m.d.sync += self.bit_index.eq(0)
                        m.d.sync += self.tx.eq(0)

                    with m.Else():
                        m.d.sync += self.done_o.eq(1)
        return m
