from amaranth import *


class UARTReceiver(Elaboratable):
    def __init__(self, clocks_per_baud):
        self.clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.rx = Signal()
        self.data_o = Signal(8, reset=0)
        self.valid_o = Signal(1, reset=0)

        # Internal Signals
        self.busy = Signal()
        self.bit_index = Signal(range(10))
        self.baud_counter = Signal(range(2 * clocks_per_baud))

        self.rx_d = Signal()
        self.rx_q = Signal()
        self.rx_q_prev = Signal()

    def elaborate(self, platform):
        m = Module()

        # Two Flip-Flop Synchronizer
        m.d.sync += [
            self.rx_d.eq(self.rx),
            self.rx_q.eq(self.rx_d),
            self.rx_q_prev.eq(self.rx_q),
        ]

        m.d.sync += self.valid_o.eq(0)

        with m.If(~self.busy):
            with m.If((~self.rx_q) & (self.rx_q_prev)):
                m.d.sync += self.busy.eq(1)
                m.d.sync += self.bit_index.eq(8)
                m.d.sync += self.baud_counter.eq(
                    self.clocks_per_baud + (self.clocks_per_baud // 2) - 2
                )

        with m.Else():
            with m.If(self.baud_counter == 0):
                with m.If(self.bit_index == 0):
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.busy.eq(0)
                    m.d.sync += self.bit_index.eq(0)
                    m.d.sync += self.baud_counter.eq(0)

                with m.Else():
                    # m.d.sync += self.data_o.eq(Cat(self.rx_q, self.data_o[0:7]))
                    m.d.sync += self.data_o.eq(Cat(self.data_o[1:8], self.rx_q))
                    m.d.sync += self.bit_index.eq(self.bit_index - 1)
                    m.d.sync += self.baud_counter.eq(self.clocks_per_baud - 1)

            with m.Else():
                m.d.sync += self.baud_counter.eq(self.baud_counter - 1)

        return m
