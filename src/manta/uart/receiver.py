from amaranth import *


class UARTReceiver(Elaboratable):
    """
    A module for receiving bytes on a 8N1 UART at a configurable baudrate.
    Outputs bytes as a stream.
    """

    def __init__(self, clocks_per_baud):
        self._clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.rx = Signal()
        self.data_o = Signal(8)
        self.valid_o = Signal(1)

        # Internal Signals
        self._busy = Signal()
        self._bit_index = Signal(range(10))
        self._baud_counter = Signal(range(2 * clocks_per_baud))

        self._rx_d = Signal()
        self._rx_q = Signal()
        self._rx_q_prev = Signal()

    def elaborate(self, platform):
        m = Module()

        # Two Flip-Flop Synchronizer
        m.d.sync += [
            self._rx_d.eq(self.rx),
            self._rx_q.eq(self._rx_d),
            self._rx_q_prev.eq(self._rx_q),
        ]

        m.d.sync += self.valid_o.eq(0)

        with m.If(~self._busy):
            with m.If((~self._rx_q) & (self._rx_q_prev)):
                m.d.sync += self._busy.eq(1)
                m.d.sync += self._bit_index.eq(8)
                m.d.sync += self._baud_counter.eq(
                    self._clocks_per_baud + (self._clocks_per_baud // 2) - 2
                )

        with m.Else():
            with m.If(self._baud_counter == 0):
                with m.If(self._bit_index == 0):
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self._busy.eq(0)
                    m.d.sync += self._bit_index.eq(0)
                    m.d.sync += self._baud_counter.eq(0)

                with m.Else():
                    # m.d.sync += self.data_o.eq(Cat(self._rx_q, self.data_o[0:7]))
                    m.d.sync += self.data_o.eq(Cat(self.data_o[1:8], self._rx_q))
                    m.d.sync += self._bit_index.eq(self._bit_index - 1)
                    m.d.sync += self._baud_counter.eq(self._clocks_per_baud - 1)

            with m.Else():
                m.d.sync += self._baud_counter.eq(self._baud_counter - 1)

        return m
