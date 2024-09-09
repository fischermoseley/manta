from amaranth import *
from amaranth.lib.enum import IntEnum

from manta.io_core import IOCore


class LogicAnalyzerTriggerBlock(Elaboratable):
    """
    A module containing an instance of a LogicAnalyzerTrigger for each input
    probe. The operations and arguments of these LogicAnalyzerTriggers are set
    with an internal IOCore, which is connected to the internal bus, and allows
    the triggers to be reprogrammed without reflashing the FPGA.
    """

    def __init__(self, probes, base_addr, interface):
        # Instantiate a bunch of trigger blocks
        self._probes = probes
        self._triggers = [LogicAnalyzerTrigger(p) for p in self._probes]

        # Make IO core for everything
        ops = [t.op for t in self._triggers]
        args = [t.arg for t in self._triggers]
        self.registers = IOCore(outputs=ops + args)
        self.registers.base_addr = base_addr
        self.registers.interface = interface

        # Bus Input/Output
        self.bus_i = self.registers.bus_i
        self.bus_o = self.registers.bus_o

        # Global trigger. High if any probe is triggered.
        self.trig = Signal()

    @property
    def max_addr(self):
        return self.registers.max_addr

    def set_triggers(self, triggers):
        # Reset all triggers to disabled with no argument
        for p in self._probes:
            self.registers.set_probe(p.name + "_op", Operations.DISABLE)
            self.registers.set_probe(p.name + "_arg", 0)

        # Set triggers
        for trigger in triggers:
            # Handle triggers that don't need an argument
            if len(trigger) == 2:
                name, op = trigger
                self.registers.set_probe(name + "_op", Operations[op].value)

            # Handle triggers that do need an argument
            elif len(trigger) == 3:
                name, op, arg = trigger
                self.registers.set_probe(name + "_op", Operations[op].value)
                self.registers.set_probe(name + "_arg", int(arg))

    def elaborate(self, platform):
        m = Module()

        # Add IO Core as submodule
        m.submodules.registers = self.registers

        # Add triggers as submodules
        for t in self._triggers:
            m.submodules[t.signal.name + "_trigger"] = t

        m.d.comb += self.trig.eq(Cat([t.triggered for t in self._triggers]).any())

        return m


class Operations(IntEnum):
    DISABLE = 0
    RISING = 1
    FALLING = 2
    CHANGING = 3
    GT = 4
    LT = 5
    GEQ = 6
    LEQ = 7
    EQ = 8
    NEQ = 9


class LogicAnalyzerTrigger(Elaboratable):
    """
    A module containing a programmable "trigger" for a given input signal,
    which asserts its output when the programmed "trigger condition" is met.
    This condition is programmed through the `op` and `arg` inputs.
    """

    def __init__(self, signal):
        self.signal = signal
        self.op = Signal(Operations, name=signal.name + "_op")
        self.arg = Signal(len(signal), name=signal.name + "_arg")
        self.triggered = Signal()

    def elaborate(self, platform):
        m = Module()

        # Save previous value to register for edge detection
        prev = Signal().like(self.signal)
        m.d.sync += prev.eq(self.signal)

        with m.If(self.op == Operations.DISABLE):
            m.d.comb += self.triggered.eq(0)

        with m.Elif(self.op == Operations.RISING):
            m.d.comb += self.triggered.eq(self.signal > prev)

        with m.Elif(self.op == Operations.FALLING):
            m.d.comb += self.triggered.eq(self.signal < prev)

        with m.Elif(self.op == Operations.CHANGING):
            m.d.comb += self.triggered.eq(self.signal != prev)

        with m.Elif(self.op == Operations.GT):
            m.d.comb += self.triggered.eq(self.signal > self.arg)

        with m.Elif(self.op == Operations.LT):
            m.d.comb += self.triggered.eq(self.signal < self.arg)

        with m.Elif(self.op == Operations.GEQ):
            m.d.comb += self.triggered.eq(self.signal >= self.arg)

        with m.Elif(self.op == Operations.LEQ):
            m.d.comb += self.triggered.eq(self.signal <= self.arg)

        with m.Elif(self.op == Operations.EQ):
            m.d.comb += self.triggered.eq(self.signal == self.arg)

        with m.Elif(self.op == Operations.NEQ):
            m.d.comb += self.triggered.eq(self.signal != self.arg)

        with m.Else():
            m.d.comb += self.triggered.eq(0)

        return m
