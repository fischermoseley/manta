from amaranth import *
from ..io_core import IOCore
from ..utils import *


class LogicAnalyzerTriggerBlock(Elaboratable):
    def __init__(self, probes, base_addr, interface):
        # Instantiate a bunch of trigger blocks
        self.probes = probes
        self.triggers = [LogicAnalyzerTrigger(p) for p in self.probes]

        # Make IO core for everything
        outputs = {}
        for p in self.probes:
            outputs[p.name + "_arg"] = p.width
            outputs[p.name + "_op"] = 4

        self.r = IOCore({"outputs": outputs}, base_addr, interface)

        # Bus Input/Output
        self.bus_i = self.r.bus_i
        self.bus_o = self.r.bus_o

        # Global trigger. High if any probe is triggered.
        self.trig = Signal(1)

    def get_max_addr(self):
        return self.r.get_max_addr()

    def set_triggers(self, config):
        # reset all triggers to zero
        for p in self.probes:
            self.r.set_probe(p.name + "_op", 0)
            self.r.set_probe(p.name + "_arg", 0)

        # set triggers
        for trigger in config["triggers"]:
            components = trigger.strip().split(" ")

            # Handle triggers that don't need an argument
            if len(components) == 2:
                name, op = components
                self.r.set_probe(name + "_op", self.triggers[0].operations[op])

            # Handle triggers that do need an argument
            elif len(components) == 3:
                name, op, arg = components
                self.r.set_probe(name + "_op", self.triggers[0].operations[op])
                self.r.set_probe(name + "_arg", int(arg))

    def elaborate(self, platform):
        m = Module()

        # Add IO Core as submodule
        m.submodules["registers"] = self.r

        # Add triggers as submodules
        for t in self.triggers:
            m.submodules[t.signal.name + "_trigger"] = t

        # Connect IO core registers to triggers
        for probe, trigger in zip(self.probes, self.triggers):
            m.d.comb += trigger.arg.eq(getattr(self.r, probe.name + "_arg"))
            m.d.comb += trigger.op.eq(getattr(self.r, probe.name + "_op"))

        m.d.comb += self.trig.eq(Cat([t.triggered for t in self.triggers]).any())

        return m


class LogicAnalyzerTrigger(Elaboratable):
    def __init__(self, signal):
        self.operations = {
            "DISABLE": 0,
            "RISING": 1,
            "FALLING": 2,
            "CHANGING": 3,
            "GT": 4,
            "LT": 5,
            "GEQ": 6,
            "LEQ": 7,
            "EQ": 8,
            "NEQ": 9,
        }

        self.signal = signal
        self.op = Signal(range(len(self.operations)))
        self.arg = Signal().like(signal)
        self.triggered = Signal(1)

    def elaborate(self, platform):
        m = Module()

        # Save previous value to register for edge detection
        prev = Signal().like(self.signal)
        m.d.sync += prev.eq(self.signal)

        with m.If(self.op == self.operations["DISABLE"]):
            m.d.comb += self.triggered.eq(0)

        with m.Elif(self.op == self.operations["RISING"]):
            m.d.comb += self.triggered.eq((self.signal) & (~prev))

        with m.Elif(self.op == self.operations["FALLING"]):
            m.d.comb += self.triggered.eq((~self.signal) & (prev))

        with m.Elif(self.op == self.operations["CHANGING"]):
            m.d.comb += self.triggered.eq(self.signal != prev)

        with m.Elif(self.op == self.operations["GT"]):
            m.d.comb += self.triggered.eq(self.signal > self.arg)

        with m.Elif(self.op == self.operations["LT"]):
            m.d.comb += self.triggered.eq(self.signal < self.arg)

        with m.Elif(self.op == self.operations["GEQ"]):
            m.d.comb += self.triggered.eq(self.signal >= self.arg)

        with m.Elif(self.op == self.operations["LEQ"]):
            m.d.comb += self.triggered.eq(self.signal <= self.arg)

        with m.Elif(self.op == self.operations["EQ"]):
            m.d.comb += self.triggered.eq(self.signal == self.arg)

        with m.Elif(self.op == self.operations["NEQ"]):
            m.d.comb += self.triggered.eq(self.signal != self.arg)

        with m.Else():
            m.d.comb += self.triggered.eq(0)

        return m
