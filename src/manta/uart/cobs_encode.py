from amaranth import *
from amaranth.lib import wiring
from amaranth.lib.memory import Memory
from amaranth.lib.wiring import In, Out

from manta.utils import *


class COBSEncode(wiring.Component):
    sink: In(StreamSignature(8))
    source: Out(StreamSignature(8, has_last=False))

    def elaborate(self, platform):
        m = Module()

        # Internal Signals
        head_pointer = Signal(range(256))
        tail_pointer = Signal(range(256))

        # Add memory and read/write ports
        m.submodules.memory = memory = Memory(shape=8, depth=256, init=[0] * 256)
        rd_port = memory.read_port()
        wr_port = memory.write_port()

        # Reset top-level IO
        m.d.sync += self.source.data.eq(0)
        m.d.sync += self.source.valid.eq(0)

        # Generate rd_port_addr_prev
        rd_port_addr_prev = Signal().like(rd_port.addr)
        m.d.sync += rd_port_addr_prev.eq(rd_port.addr)

        # State Machine:
        with m.FSM() as fsm:
            with m.State("IDLE"):
                with m.If(self.sink.last):
                    m.d.sync += head_pointer.eq(0)
                    m.d.sync += tail_pointer.eq(0)
                    m.d.sync += rd_port.addr.eq(0)
                    m.next = "SEARCH_FOR_ZERO"

            with m.State("SEARCH_FOR_ZERO"):
                # Drive read addr until length is reached
                with m.If(rd_port.addr < wr_port.addr):
                    m.d.sync += rd_port.addr.eq(rd_port.addr + 1)

                # Watch prev_addr and data
                with m.If((rd_port_addr_prev == wr_port.addr) | (rd_port.data == 0)):
                    # Either reached the end of the input buffer or found a zero

                    m.d.sync += head_pointer.eq(rd_port_addr_prev)
                    m.d.sync += rd_port.addr.eq(tail_pointer)
                    m.d.sync += self.source.data.eq(
                        rd_port_addr_prev - tail_pointer + 1
                    )
                    m.d.sync += self.source.valid.eq(1)

                    m.next = "CLOCK_OUT_BYTES_STALL"

                with m.Else():
                    m.next = "SEARCH_FOR_ZERO"

            with m.State("CLOCK_OUT_BYTES_STALL"):
                m.d.sync += rd_port.addr.eq(rd_port.addr + 1)
                m.next = "CLOCK_OUT_BYTES"

            with m.State("CLOCK_OUT_BYTES"):
                # Drive rd_port.addr
                with m.If(rd_port.addr < head_pointer):
                    m.d.sync += rd_port.addr.eq(rd_port.addr + 1)

                # Watch prev_addr
                with m.If(rd_port_addr_prev < head_pointer):
                    m.d.sync += self.source.data.eq(rd_port.data)
                    m.d.sync += self.source.valid.eq(1)
                    m.next = "CLOCK_OUT_BYTES"

                with m.If(rd_port_addr_prev == head_pointer):
                    # Reached end of message
                    with m.If(head_pointer == wr_port.addr):
                        m.d.sync += self.source.data.eq(0)
                        m.d.sync += self.source.valid.eq(1)

                        m.next = "IDLE"

                    with m.Else():  # this section is a beautiful!
                        m.d.sync += tail_pointer.eq(head_pointer + 1)
                        m.d.sync += head_pointer.eq(head_pointer + 1)
                        m.d.sync += rd_port.addr.eq(head_pointer + 1)
                        m.d.sync += self.source.valid.eq(
                            0
                        )  # i have no idea why this works

                        m.next = "SEARCH_FOR_ZERO_STALL"

            with m.State("SEARCH_FOR_ZERO_STALL"):
                m.next = "SEARCH_FOR_ZERO"

        # Fill memory from input stream
        m.d.comb += wr_port.en.eq((fsm.ongoing("IDLE")) & (self.sink.valid))
        m.d.comb += wr_port.data.eq(self.sink.data)
        m.d.sync += wr_port.addr.eq(wr_port.addr + wr_port.en)

        m.d.comb += self.sink.ready.eq(fsm.ongoing("IDLE"))

        return m
