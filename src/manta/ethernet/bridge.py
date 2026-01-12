from amaranth import *

from manta.utils import *


class EthernetBridge(Elaboratable):
    def __init__(self):
        self.data_i = Signal(32)
        self.valid_i = Signal()
        self.last_i = Signal()
        self.ready_o = Signal()

        self.data_o = Signal(32)
        self.valid_o = Signal()
        self.last_o = Signal()
        self.ready_i = Signal()

        self.bus_o = Signal(InternalBus())
        self.bus_i = Signal(InternalBus())

    def elaborate(self, platform):
        m = Module()

        seq_num_expected = Signal(13)
        read_len = Signal(7)

        with m.FSM(init="IDLE"):
            with m.State("IDLE"):
                m.d.sync += self.ready_o.eq(1)
                m.d.sync += self.valid_o.eq(0)

                # TODO: not necessary, but makes debugging way easier
                m.d.sync += self.last_o.eq(0)
                m.d.sync += self.data_o.eq(0)

                with m.If(self.valid_i & self.ready_o):
                    # First 32 bits was presented, which contains message type (first 3 bits)
                    # as well as sequence number (next 13 bits). The remaining 16 bits are unused.

                    # Send NACK if message type or sequence number is incorrect
                    with m.If(
                        (self.data_i[:3] > max(MessageTypes))
                        | (self.data_i[3:16] != seq_num_expected)
                    ):
                        # Wait to NACK if this isn't the last beat in message
                        with m.If(~self.last_i):
                            m.next = "NACK_WAIT_FOR_LAST"

                        # Otherwise, NACK immediately
                        with m.Else():
                            m.d.sync += self.data_o.eq(
                                Cat(
                                    C(0, unsigned(16)),
                                    seq_num_expected,
                                    MessageTypes.NACK,
                                )
                            )
                            m.d.sync += self.valid_o.eq(1)
                            m.d.sync += self.last_o.eq(1)
                            m.d.sync += self.ready_o.eq(0)
                            m.next = "NACK_WAIT_FOR_READY"

                    with m.Elif(self.data_i[:3] == MessageTypes.READ_REQUEST):
                        m.d.sync += seq_num_expected.eq(seq_num_expected + 1)
                        m.d.sync += read_len.eq(self.data_i[16:23] - 1)

                        m.d.sync += self.data_o.eq(
                            Cat(
                                C(0, unsigned(16)),
                                seq_num_expected,
                                MessageTypes.READ_RESPONSE,
                            )
                        )
                        m.d.sync += self.valid_o.eq(1)
                        m.next = "READ_WAIT_FOR_ADDR"

                    with m.Elif(self.data_i[:3] == MessageTypes.WRITE_REQUEST):
                        m.next = "WRITE_WAIT_FOR_ADDR"

            with m.State("READ_WAIT_FOR_ADDR"):
                m.d.sync += self.valid_o.eq(0)
                m.d.sync += self.data_o.eq(0)

                with m.If(self.valid_i):
                    # we have the length and the address to read from, let's go!
                    m.d.sync += self.bus_o.addr.eq(self.data_i)
                    m.d.sync += self.bus_o.data.eq(0)
                    m.d.sync += self.bus_o.rw.eq(0)
                    m.d.sync += self.bus_o.valid.eq(1)

                    with m.If(read_len == 0):
                        # we've sent the last read request in this batch to the bus
                        m.d.sync += self.bus_o.last.eq(1)
                        m.d.sync += read_len.eq(0)

                    m.next = "READ"

            with m.State("READ"):
                m.d.sync += self.ready_o.eq(0)

                # Clock out read requests to the bus
                with m.If(read_len > 0):
                    m.d.sync += self.bus_o.addr.eq(self.bus_o.addr + 1)
                    m.d.sync += read_len.eq(read_len - 1)

                    with m.If(read_len == 1):
                        m.d.sync += self.bus_o.last.eq(1)

                with m.Else():
                    m.d.sync += self.bus_o.eq(
                        0
                    )  # TODO: it's probably overzealous to set the whole bus to zero, but it makes debugging easy so we're doing it xD

                # Clock out any read data from the bus
                with m.If(self.bus_i.valid):
                    m.d.sync += self.data_o.eq(self.bus_i.data)
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.last_o.eq(self.bus_i.last)

                with m.If(self.last_o):
                    m.d.sync += self.data_o.eq(0)
                    m.d.sync += self.valid_o.eq(0)
                    m.d.sync += self.last_o.eq(0)
                    m.next = "IDLE"  # TODO: could save a cycle by checking valid_i to see if there's more work to do

            with m.State("WRITE_WAIT_FOR_ADDR"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_o.addr.eq(self.data_i)
                    m.next = "WRITE_FIRST"

            # Don't want to increment address on the first write,
            # and I'm lazy so I'm making a new state to keep track of that
            with m.State("WRITE_FIRST"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_o.data.eq(self.data_i)
                    m.d.sync += self.bus_o.rw.eq(1)
                    m.d.sync += self.bus_o.valid.eq(1)
                    m.d.sync += self.bus_o.last.eq(self.last_i)

                    with m.If(self.last_i):
                        m.d.sync += self.ready_o.eq(0)
                        m.next = "WRITE_WAIT_FOR_LAST"

                    with m.Else():
                        m.next = "WRITE"

            with m.State("WRITE"):
                with m.If(self.valid_i):
                    m.d.sync += self.bus_o.addr.eq(self.bus_o.addr + 1)
                    m.d.sync += self.bus_o.data.eq(self.data_i)
                    m.d.sync += self.bus_o.rw.eq(1)
                    m.d.sync += self.bus_o.valid.eq(1)
                    m.d.sync += self.bus_o.last.eq(self.last_i)

                    with m.If(self.last_i):
                        m.d.sync += self.ready_o.eq(0)
                        m.next = "WRITE_WAIT_FOR_LAST"

                    with m.Else():
                        m.next = "WRITE"

                with m.Else():
                    m.next = "WRITE"

            with m.State("WRITE_WAIT_FOR_LAST"):
                m.d.sync += self.bus_o.eq(0)

                with m.If(self.bus_i.last):
                    m.d.sync += seq_num_expected.eq(seq_num_expected + 1)

                    m.d.sync += self.data_o.eq(
                        Cat(
                            C(0, unsigned(16)),
                            seq_num_expected,
                            MessageTypes.WRITE_RESPONSE,
                        )
                    )
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.last_o.eq(1)
                    m.next = "IDLE"  # TODO: could save a cycle by checking valid_i to see if there's more work to do

            with m.State("NACK_WAIT_FOR_LAST"):
                with m.If(self.last_i):
                    m.d.sync += self.data_o.eq(
                        Cat(C(0, unsigned(16)), seq_num_expected, MessageTypes.NACK)
                    )
                    m.d.sync += self.valid_o.eq(1)
                    m.d.sync += self.last_o.eq(1)
                    m.d.sync += self.ready_o.eq(0)
                    m.next = "NACK_WAIT_FOR_READY"

            with m.State("NACK_WAIT_FOR_READY"):
                with m.If(self.ready_i):
                    m.d.sync += self.valid_o.eq(0)

                    # TODO: remove these next two lines, they're not necessary
                    # although they are nice for debug...
                    m.d.sync += self.data_o.eq(0)
                    m.d.sync += self.last_o.eq(0)
                    m.d.sync += self.ready_o.eq(1)

                    m.next = "IDLE"

        return m
