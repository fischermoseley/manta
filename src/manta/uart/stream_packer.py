from amaranth import *


class StreamPacker(Elaboratable):
    def __init__(self):
        self.data_i = Signal(8)
        self.valid_i = Signal()
        self.last_i = Signal()

        self.data_o = Signal(32)
        self.valid_o = Signal()
        self.ready_i = Signal()
        self.last_o = Signal()

    def elaborate(self, platform):
        m = Module()
        return m
