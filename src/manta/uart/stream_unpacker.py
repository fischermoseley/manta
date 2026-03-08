from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.wiring import In, Out

from manta.utils import *


class StreamUnpacker(wiring.Component):
    sink: In(StreamSignature(32))
    source: Out(StreamSignature(8))

    def elaborate(self, platform):
        m = Module()

        # Turn a stream of 32-bit numbers into a stream of 8-bit numbers

        # Defining an internal idle signal and combinationally assigning it to
        # self.sink.ready allows us to specify an initial value for the signal
        # without having to modify the members of StreamSignature
        idle = Signal(init=1)
        m.d.comb += self.sink.ready.eq(idle)

        buf = Signal(24)
        last = Signal()
        count = Signal(range(3))

        with m.If(idle):
            with m.If(self.sink.valid):
                m.d.sync += buf.eq(self.sink.data[8:])
                m.d.sync += last.eq(self.sink.last)
                m.d.sync += idle.eq(0)

                m.d.sync += self.source.data.eq(self.sink.data[:7])
                m.d.sync += self.source.valid.eq(1)

                m.d.sync += count.eq(0)

        # Have some data in the buffer
        with m.Else():
            with m.If(self.source.valid & self.source.ready):
                # if done, clean up and signal ready for next word
                with m.If(count == 3):
                    m.d.sync += self.source.valid.eq(0)
                    m.d.sync += idle.eq(1)

                    # TODO: not necessary, but makes debugging much easier!
                    m.d.sync += self.source.data.eq(0)
                    m.d.sync += self.source.last.eq(0)

                # if not done, clock out next byte
                with m.Else():
                    m.d.sync += self.source.data.eq(buf[:8])
                    m.d.sync += buf.eq(buf >> 8)
                    m.d.sync += count.eq(count + 1)

                    m.d.sync += self.source.last.eq((last) & (count == 2))
        return m
