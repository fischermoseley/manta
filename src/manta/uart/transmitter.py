from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class UARTTransmitter(wiring.Component):
    """
    A module for transmitting bytes on a 8N1 UART at a configurable baudrate.
    Accepts bytes as a stream.
    """

    sink: In(StreamSignature(8, has_last=False))
    tx: Out(1, init=1)

    def __init__(self, clocks_per_baud):
        super().__init__()
        self._clocks_per_baud = clocks_per_baud

    def elaborate(self, platform):
        m = Module()

        # Defining an internal idle signal and combinationally assigning it to
        # self.sink.ready allows us to specify an initial value for the signal
        # without having to modify the members of StreamSignature
        idle = Signal(init=1)
        m.d.comb += self.sink.ready.eq(idle)

        baud_counter = Signal(range(self._clocks_per_baud))
        buffer = Signal(9)
        bit_index = Signal(4)

        with m.If(idle):
            with m.If(self.sink.valid):
                m.d.sync += baud_counter.eq(self._clocks_per_baud - 1)
                m.d.sync += buffer.eq(Cat(self.sink.data, 1))
                m.d.sync += bit_index.eq(0)
                m.d.sync += idle.eq(0)
                m.d.sync += self.tx.eq(0)

        with m.Else():
            m.d.sync += baud_counter.eq(baud_counter - 1)
            m.d.sync += idle.eq((baud_counter == 1) & (bit_index == 9))

            # A baud period has elapsed
            with m.If(baud_counter == 0):
                m.d.sync += baud_counter.eq(self._clocks_per_baud - 1)

                # Clock out another bit if there are any left
                with m.If(bit_index < 9):
                    m.d.sync += self.tx.eq(buffer.bit_select(bit_index, 1))
                    m.d.sync += bit_index.eq(bit_index + 1)

                # Byte has been sent, send out next one or go to idle
                with m.Else():
                    with m.If(self.sink.valid):
                        m.d.sync += buffer.eq(Cat(self.sink.data, 1))
                        m.d.sync += bit_index.eq(0)
                        m.d.sync += self.tx.eq(0)

                    with m.Else():
                        m.d.sync += idle.eq(1)
        return m
