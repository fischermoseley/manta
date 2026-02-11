from amaranth import *


class StreamUnpacker(Elaboratable):
    def __init__(self):
        self.data_i = Signal(32)
        self.valid_i = Signal()
        self.ready_o = Signal(init=1)
        self.last_i = Signal()

        self.data_o = Signal(8)
        self.valid_o = Signal()
        self.ready_i = Signal()
        self.last_o = Signal()

    def elaborate(self, platform):
        m = Module()

        # Turn a stream of 32-bit numbers into a stream of 8-bit numbers
        buf = Signal(24)
        last = Signal()
        count = Signal(range(3))

        with m.If(self.ready_o):
            with m.If(self.valid_i):
                m.d.sync += buf.eq(self.data_i[8:])
                m.d.sync += last.eq(self.last_i)
                m.d.sync += self.ready_o.eq(0)

                m.d.sync += self.data_o.eq(self.data_i[:7])
                m.d.sync += self.valid_o.eq(1)

                m.d.sync += count.eq(0)

        # Have some data in the buffer
        with m.Else():
            with m.If(self.valid_o & self.ready_i):
                # if done, clean up and signal ready for next word
                with m.If(count == 3):
                    m.d.sync += self.valid_o.eq(0)
                    m.d.sync += self.ready_o.eq(1)

                    # TODO: not necessary, but makes debugging much easier!
                    m.d.sync += self.data_o.eq(0)
                    m.d.sync += self.last_o.eq(0)

                # if not done, clock out next byte
                with m.Else():
                    m.d.sync += self.data_o.eq(buf[8:])
                    m.d.sync += buf.eq(buf >> 8)
                    m.d.sync += count.eq(count + 1)

                    m.d.sync += self.last_o.eq((last) & (count == 2))
        return m
