from amaranth import *


class TransmitBridge(Elaboratable):
    """
    A module for bridging Manta's internal bus to the stream of bytes expected
    by the UARTTransmitter module.
    """

    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(16)
        self.rw_i = Signal()
        self.valid_i = Signal()

        self.data_o = Signal(8)
        self.start_o = Signal(1)
        self.done_i = Signal()

        # Internal Signals
        self._buffer = Signal(16)
        self._count = Signal(4)
        self._busy = Signal(1)
        self._to_ascii_hex = Signal(8)
        self._n = Signal(4)

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.start_o.eq(self._busy)

        with m.If(~self._busy):
            with m.If((self.valid_i) & (~self.rw_i)):
                m.d.sync += self._busy.eq(1)
                m.d.sync += self._buffer.eq(self.data_i)

        with m.Else():
            # uart_tx is transmitting a byte:
            with m.If(self.done_i):
                m.d.sync += self._count.eq(self._count + 1)

                # Message has been transmitted
                with m.If(self._count > 5):
                    m.d.sync += self._count.eq(0)

                    # Go back to idle, or transmit next message
                    with m.If((self.valid_i) & (~self.rw_i)):
                        m.d.sync += self._buffer.eq(self.data_i)

                    with m.Else():
                        m.d.sync += self._busy.eq(0)

        # define to_ascii_hex
        with m.If(self._n < 10):
            m.d.comb += self._to_ascii_hex.eq(self._n + 0x30)
        with m.Else():
            m.d.comb += self._to_ascii_hex.eq(self._n + 0x41 - 10)

        # run the sequence
        with m.If(self._count == 0):
            m.d.comb += self._n.eq(0)
            m.d.comb += self.data_o.eq(ord("D"))

        with m.Elif(self._count == 1):
            m.d.comb += self._n.eq(self._buffer[12:16])
            m.d.comb += self.data_o.eq(self._to_ascii_hex)

        with m.Elif(self._count == 2):
            m.d.comb += self._n.eq(self._buffer[8:12])
            m.d.comb += self.data_o.eq(self._to_ascii_hex)

        with m.Elif(self._count == 3):
            m.d.comb += self._n.eq(self._buffer[4:8])
            m.d.comb += self.data_o.eq(self._to_ascii_hex)

        with m.Elif(self._count == 4):
            m.d.comb += self._n.eq(self._buffer[0:4])
            m.d.comb += self.data_o.eq(self._to_ascii_hex)

        with m.Elif(self._count == 5):
            m.d.comb += self._n.eq(0)
            m.d.comb += self.data_o.eq(ord("\r"))

        with m.Elif(self._count == 6):
            m.d.comb += self._n.eq(0)
            m.d.comb += self.data_o.eq(ord("\n"))

        with m.Else():
            m.d.comb += self._n.eq(0)
            m.d.comb += self.data_o.eq(0)

        return m
