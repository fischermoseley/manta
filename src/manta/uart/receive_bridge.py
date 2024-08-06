from amaranth import *
from amaranth.lib.data import ArrayLayout
from amaranth.lib.enum import IntEnum


class States(IntEnum):
    IDLE = 0
    READ = 1
    WRITE = 2


class ReceiveBridge(Elaboratable):
    """
    A module for bridging the stream of bytes from the UARTReceiver module to
    Manta's internal bus.
    """

    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(8)
        self.valid_i = Signal()

        self.addr_o = Signal(16)
        self.data_o = Signal(16)
        self.rw_o = Signal(1)
        self.valid_o = Signal(1)

        # Internal Signals
        self._buffer = Signal(ArrayLayout(4, 8))
        self._state = Signal(States)
        self._byte_num = Signal(4)
        self._is_eol = Signal()
        self._is_ascii_hex = Signal()
        self._from_ascii_hex = Signal(8)

    def _drive_ascii_signals(self, m):
        # Decode 0-9
        with m.If((self.data_i >= 0x30) & (self.data_i <= 0x39)):
            m.d.comb += self._is_ascii_hex.eq(1)
            m.d.comb += self._from_ascii_hex.eq(self.data_i - 0x30)

        # Decode A-F
        with m.Elif((self.data_i >= 0x41) & (self.data_i <= 0x46)):
            m.d.comb += self._is_ascii_hex.eq(1)
            m.d.comb += self._from_ascii_hex.eq(self.data_i - 0x41 + 10)

        with m.Else():
            m.d.comb += self._is_ascii_hex.eq(0)
            m.d.comb += self._from_ascii_hex.eq(0)

        with m.If((self.data_i == ord("\r")) | (self.data_i == ord("\n"))):
            m.d.comb += self._is_eol.eq(1)

        with m.Else():
            m.d.comb += self._is_eol.eq(0)

    def _drive_output_bus(self, m):
        with m.If(
            (self._state == States.READ) & (self._byte_num == 4) & (self._is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self._buffer[3], self._buffer[2], self._buffer[1], self._buffer[0])
            )
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(0)

        with m.Elif(
            (self._state == States.WRITE) & (self._byte_num == 8) & (self._is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self._buffer[3], self._buffer[2], self._buffer[1], self._buffer[0])
            )
            m.d.comb += self.data_o.eq(
                Cat(self._buffer[7], self._buffer[6], self._buffer[5], self._buffer[4])
            )
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(1)

        with m.Else():
            m.d.comb += self.addr_o.eq(0)
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.rw_o.eq(0)
            m.d.comb += self.valid_o.eq(0)

    def _drive_fsm(self, m):
        with m.If(self.valid_i):
            with m.If(self._state == States.IDLE):
                m.d.sync += self._byte_num.eq(0)

                with m.If(self.data_i == ord("R")):
                    m.d.sync += self._state.eq(States.READ)

                with m.Elif(self.data_i == ord("W")):
                    m.d.sync += self._state.eq(States.WRITE)

            with m.If(self._state == States.READ):
                # buffer bytes if we don't have enough
                with m.If(self._byte_num < 4):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self._is_ascii_hex == 0):
                        m.d.sync += self._state.eq(States.IDLE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self._buffer[self._byte_num].eq(
                            self._from_ascii_hex
                        )
                        m.d.sync += self._byte_num.eq(self._byte_num + 1)

                with m.Else():
                    m.d.sync += self._state.eq(States.IDLE)

            with m.If(self._state == States.WRITE):
                # buffer bytes if we don't have enough
                with m.If(self._byte_num < 8):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self._is_ascii_hex == 0):
                        m.d.sync += self._state.eq(States.IDLE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self._buffer[self._byte_num].eq(
                            self._from_ascii_hex
                        )
                        m.d.sync += self._byte_num.eq(self._byte_num + 1)

                with m.Else():
                    m.d.sync += self._state.eq(States.IDLE)
        pass

    def elaborate(self, platform):
        m = Module()

        self._drive_ascii_signals(m)
        self._drive_output_bus(m)
        self._drive_fsm(m)

        return m
