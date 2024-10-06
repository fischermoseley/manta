from amaranth import *
from amaranth.lib.memory import Memory

class COBSEncoder(Elaboratable):
    def __init__(self):

        # Top-Level IO
        self.start = Signal(1)
        self.done = Signal(1)

        # Stream-like data input
        self.data_in = Signal(8)
        self.data_in_valid = Signal(1)

        # Stream-like data output
        self.data_out = Signal(8)
        self.data_out_valid = Signal(1)

        # Define memory
        self.memory = Memory(shape=8, depth=256, init = [0]*256)

    def elaborate(self, platform):
        m = Module()

        # Internal Signals
        head_pointer =  Signal(range(256))
        tail_pointer = Signal(range(256))

        # Add memory and read/write ports
        m.submodules.memory = self.memory
        rd_port = self.memory.read_port()
        wr_port = self.memory.write_port()

        # Reset top-level IO
        m.d.sync += self.data_out.eq(0)
        m.d.sync += self.data_out_valid.eq(0)

        # Generate rd_port_addr_prev
        rd_port_addr_prev = Signal().like(rd_port.addr)
        m.d.sync += rd_port_addr_prev.eq(rd_port.addr)

        # State Machine:
        with m.FSM() as fsm:
            with m.State("IDLE"):
                with m.If(self.start):
                    m.d.sync += head_pointer.eq(0)
                    m.d.sync += tail_pointer.eq(0)
                    m.d.sync += rd_port.addr.eq(0)
                    m.next = "SFZ"

            with m.State("SFZ"):
                # Drive read addr until length is reached
                with m.If(rd_port.addr < wr_port.addr):
                    m.d.sync += rd_port.addr.eq(rd_port.addr + 1)

                # Watch prev_addr and data
                with m.If((rd_port_addr_prev == wr_port.addr) | (rd_port.data == 0)):
                    # Either reached the end of the input buffer or found a zero

                    m.d.sync += head_pointer.eq(rd_port_addr_prev)
                    m.d.sync += rd_port.addr.eq(tail_pointer)
                    m.d.sync += self.data_out.eq(rd_port_addr_prev - tail_pointer + 1)
                    m.d.sync += self.data_out_valid.eq(1)

                    m.next = "COB_STALL"

                with m.Else():
                    m.next = "SFZ"

            with m.State("COB_STALL"):
                m.d.sync += rd_port.addr.eq(rd_port.addr + 1)
                m.next = "COB"

            with m.State("COB"):
                # Drive rd_port.addr
                with m.If(rd_port.addr < head_pointer):
                    m.d.sync += rd_port.addr.eq(rd_port.addr + 1)

                # Watch prev_addr
                with m.If(rd_port_addr_prev <= head_pointer):
                    m.d.sync += self.data_out.eq(rd_port.data)
                    m.d.sync += self.data_out_valid.eq(1)
                    m.next = "COB"

                with m.If(rd_port_addr_prev == head_pointer):
                    # Reached end of message
                    with m.If(head_pointer == wr_port.addr):
                        m.d.sync += self.data_out.eq(0)
                        m.d.sync += self.data_out_valid.eq(1)

                        m.next = "IDLE"

                    with m.Else(): # this section is a beautiful!
                        m.d.sync += tail_pointer.eq(head_pointer + 1)
                        m.d.sync += head_pointer.eq(head_pointer + 1)
                        m.d.sync += rd_port.addr.eq(head_pointer + 1)
                        m.d.sync += self.data_out_valid.eq(0) # i have no idea why this works

                        m.next = "SFZ_STALL"

            with m.State("SFZ_STALL"):
                m.next = "SFZ"


        # Fill memory from input stream
        m.d.comb += wr_port.en.eq((fsm.ongoing("IDLE")) & (self.data_in_valid))
        m.d.comb += wr_port.data.eq(self.data_in)
        m.d.sync += wr_port.addr.eq(wr_port.addr + wr_port.en)

        return m



