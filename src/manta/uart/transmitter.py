from amaranth import *


class UARTTransmitter(Elaboratable):
    """
    A module for transmitting bytes on a 8N1 UART at a configurable baudrate.
    Accepts bytes as a stream.
    """

    def __init__(self, clocks_per_baud):
        self._clocks_per_baud = clocks_per_baud

        # Top-Level Ports
        self.data_i = Signal(8)
        self.start_i = Signal()
        self.done_o = Signal(init=1)

        self.tx = Signal(init=1)

        # Internal Signals
        self._baud_counter = Signal(range(self._clocks_per_baud))
        self._buffer = Signal(9)
        self._bit_index = Signal(4)

    def elaborate(self, platform):
        m = Module()

        with m.If((self.start_i) & (self.done_o)):
            m.d.sync += self._baud_counter.eq(self._clocks_per_baud - 1)
            m.d.sync += self._buffer.eq(Cat(self.data_i, 1))
            m.d.sync += self._bit_index.eq(0)
            m.d.sync += self.done_o.eq(0)
            m.d.sync += self.tx.eq(0)

        with m.Elif(~self.done_o):
            m.d.sync += self._baud_counter.eq(self._baud_counter - 1)
            m.d.sync += self.done_o.eq(
                (self._baud_counter == 1) & (self._bit_index == 9)
            )

            # A baud period has elapsed
            with m.If(self._baud_counter == 0):
                m.d.sync += self._baud_counter.eq(self._clocks_per_baud - 1)

                # Clock out another bit if there are any left
                with m.If(self._bit_index < 9):
                    m.d.sync += self.tx.eq(self._buffer.bit_select(self._bit_index, 1))
                    m.d.sync += self._bit_index.eq(self._bit_index + 1)

                # Byte has been sent, send out next one or go to idle
                with m.Else():
                    with m.If(self.start_i):
                        m.d.sync += self._buffer.eq(Cat(self.data_i, 1))
                        m.d.sync += self._bit_index.eq(0)
                        m.d.sync += self.tx.eq(0)

                    with m.Else():
                        m.d.sync += self.done_o.eq(1)
        return m
