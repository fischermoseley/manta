from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class UARTReceiver(wiring.Component):
    """
    A module for receiving bytes on a 8N1 UART at a configurable baudrate.
    Outputs bytes as a stream.
    """

    rx: In(1)
    source: Out(StreamSignature(8, has_last=False, has_ready=False))

    def __init__(self, clocks_per_baud):
        super().__init__()
        self._clocks_per_baud = clocks_per_baud

    def elaborate(self, platform):
        m = Module()

        busy = Signal()
        bit_index = Signal(range(10))
        baud_counter = Signal(range(2 * self._clocks_per_baud))

        rx_d = Signal()
        rx_q = Signal()
        rx_q_prev = Signal()

        # Two Flip-Flop Synchronizer
        m.d.sync += [
            rx_d.eq(self.rx),
            rx_q.eq(rx_d),
            rx_q_prev.eq(rx_q),
        ]

        m.d.sync += self.source.valid.eq(0)

        with m.If(~busy):
            with m.If((~rx_q) & (rx_q_prev)):
                m.d.sync += busy.eq(1)
                m.d.sync += bit_index.eq(8)
                m.d.sync += baud_counter.eq(
                    self._clocks_per_baud + (self._clocks_per_baud // 2) - 2
                )

        with m.Else():
            with m.If(baud_counter == 0):
                with m.If(bit_index == 0):
                    m.d.sync += self.source.valid.eq(1)
                    m.d.sync += busy.eq(0)
                    m.d.sync += bit_index.eq(0)
                    m.d.sync += baud_counter.eq(0)

                with m.Else():
                    m.d.sync += self.source.data.eq(Cat(self.source.data[1:8], rx_q))
                    m.d.sync += bit_index.eq(bit_index - 1)
                    m.d.sync += baud_counter.eq(self._clocks_per_baud - 1)

            with m.Else():
                m.d.sync += baud_counter.eq(baud_counter - 1)

        return m
