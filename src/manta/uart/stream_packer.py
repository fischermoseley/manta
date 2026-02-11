from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class StreamPacker(wiring.Component):
    sink: In(StreamSignature(8))
    source: Out(StreamSignature(32))

    def elaborate(self, platform):
        m = Module()

        # Defining an internal idle signal and combinationally assigning it to
        # self.sink.ready allows us to specify an initial value for the signal
        # without having to modify the members of StreamSignature
        idle = Signal(init=1)
        m.d.comb += self.sink.ready.eq(idle)

        count = Signal(range(4))

        with m.If(idle):
            with m.If(self.sink.valid):
                m.d.sync += self.source.data.eq(
                    Cat(self.source.data[8:], self.sink.data)
                )
                m.d.sync += count.eq(count + 1)

                with m.If(count == 3):
                    m.d.sync += idle.eq(0)
                    m.d.sync += self.source.valid.eq(1)
                    m.d.sync += self.source.last.eq(self.sink.last)

        with m.Else():
            with m.If(self.source.valid & self.source.ready):
                m.d.sync += idle.eq(1)
                m.d.sync += self.source.valid.eq(0)

                # TODO: not necessary, but makes debugging much easier!
                m.d.sync += self.source.data.eq(0)
                m.d.sync += self.source.last.eq(0)

        return m
