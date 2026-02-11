from amaranth import *


class StreamPacker(Elaboratable):
    def __init__(self):
        self.data_i = Signal(8)
        self.valid_i = Signal()
        self.ready_o = Signal(init=1)
        self.last_i = Signal()

        self.data_o = Signal(32)
        self.valid_o = Signal()
        self.ready_i = Signal()
        self.last_o = Signal()

    def elaborate(self, platform):
        m = Module()

        count = Signal(range(4))

        with m.If(self.ready_o):
            with m.If(self.valid_i):
                m.d.sync += self.data_o.eq(Cat(self.data_o[8:], self.data_i))
                m.d.sync += count.eq(count + 1)

                with m.If(count == 3):
                    m.d.sync += self.ready_o.eq(0)
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.last_o.eq(self.last_i)

        with m.Else():
            with m.If(self.valid_o & self.ready_i):
                m.d.sync += self.ready_o.eq(1)
                m.d.sync += self.valid_o.eq(0)

                # TODO: not necessary, but makes debugging much easier!
                m.d.sync += self.data_o.eq(0)
                m.d.sync += self.last_o.eq(0)

        return m
