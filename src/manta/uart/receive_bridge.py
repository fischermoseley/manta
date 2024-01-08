from amaranth import *
from amaranth.lib.data import ArrayLayout


class ReceiveBridge(Elaboratable):
    def __init__(self):
        # Top-Level Ports
        self.data_i = Signal(8)
        self.valid_i = Signal()

        self.addr_o = Signal(16, reset=0)
        self.data_o = Signal(16, reset=0)
        self.rw_o = Signal(1, reset=0)
        self.valid_o = Signal(1, reset=0)

        # State Machine
        self.IDLE_STATE = 0
        self.READ_STATE = 1
        self.WRITE_STATE = 2

        # Internal Signals
        self.buffer = Signal(ArrayLayout(4, 8), reset_less=True)
        self.state = Signal(2, reset=self.IDLE_STATE)
        self.byte_num = Signal(4, reset=0)
        self.is_eol = Signal()
        self.is_ascii_hex = Signal()
        self.from_ascii_hex = Signal(8)

    def drive_ascii_signals(self, m):
        # Decode 0-9
        with m.If((self.data_i >= 0x30) & (self.data_i <= 0x39)):
            m.d.comb += self.is_ascii_hex.eq(1)
            m.d.comb += self.from_ascii_hex.eq(self.data_i - 0x30)

        # Decode A-F
        with m.Elif((self.data_i >= 0x41) & (self.data_i <= 0x46)):
            m.d.comb += self.is_ascii_hex.eq(1)
            m.d.comb += self.from_ascii_hex.eq(self.data_i - 0x41 + 10)

        with m.Else():
            m.d.comb += self.is_ascii_hex.eq(0)
            m.d.comb += self.from_ascii_hex.eq(0)

        with m.If((self.data_i == ord("\r")) | (self.data_i == ord("\n"))):
            m.d.comb += self.is_eol.eq(1)

        with m.Else():
            m.d.comb += self.is_eol.eq(0)

    def drive_output_bus(self, m):
        with m.If(
            (self.state == self.READ_STATE) & (self.byte_num == 4) & (self.is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self.buffer[3], self.buffer[2], self.buffer[1], self.buffer[0])
            )
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(0)

        with m.Elif(
            (self.state == self.WRITE_STATE) & (self.byte_num == 8) & (self.is_eol)
        ):
            m.d.comb += self.addr_o.eq(
                Cat(self.buffer[3], self.buffer[2], self.buffer[1], self.buffer[0])
            )
            m.d.comb += self.data_o.eq(
                Cat(self.buffer[7], self.buffer[6], self.buffer[5], self.buffer[4])
            )
            m.d.comb += self.valid_o.eq(1)
            m.d.comb += self.rw_o.eq(1)

        with m.Else():
            m.d.comb += self.addr_o.eq(0)
            m.d.comb += self.data_o.eq(0)
            m.d.comb += self.rw_o.eq(0)
            m.d.comb += self.valid_o.eq(0)

    def drive_fsm(self, m):
        with m.If(self.valid_i):
            with m.If(self.state == self.IDLE_STATE):
                m.d.sync += self.byte_num.eq(0)

                with m.If(self.data_i == ord("R")):
                    m.d.sync += self.state.eq(self.READ_STATE)

                with m.Elif(self.data_i == ord("W")):
                    m.d.sync += self.state.eq(self.WRITE_STATE)

            with m.If(self.state == self.READ_STATE):
                # buffer bytes if we don't have enough
                with m.If(self.byte_num < 4):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self.is_ascii_hex == 0):
                        m.d.sync += self.state.eq(self.IDLE_STATE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self.buffer[self.byte_num].eq(self.from_ascii_hex)
                        m.d.sync += self.byte_num.eq(self.byte_num + 1)

                with m.Else():
                    m.d.sync += self.state.eq(self.IDLE_STATE)

            with m.If(self.state == self.WRITE_STATE):
                # buffer bytes if we don't have enough
                with m.If(self.byte_num < 8):
                    # if bytes aren't valid ASCII then return to IDLE state
                    with m.If(self.is_ascii_hex == 0):
                        m.d.sync += self.state.eq(self.IDLE_STATE)

                    # otherwise buffer them
                    with m.Else():
                        m.d.sync += self.buffer[self.byte_num].eq(self.from_ascii_hex)
                        m.d.sync += self.byte_num.eq(self.byte_num + 1)

                with m.Else():
                    m.d.sync += self.state.eq(self.IDLE_STATE)
        pass

    def elaborate(self, platform):
        m = Module()

        self.drive_ascii_signals(m)
        self.drive_output_bus(m)
        self.drive_fsm(m)

        return m
