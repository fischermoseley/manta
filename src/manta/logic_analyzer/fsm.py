from amaranth import *
from amaranth.lib.enum import IntEnum

from manta.io_core import IOCore


class States(IntEnum):
    IDLE = 0
    MOVE_TO_POSITION = 1
    IN_POSITION = 2
    CAPTURING = 3
    CAPTURED = 4


class TriggerModes(IntEnum):
    SINGLE_SHOT = 0
    INCREMENTAL = 1
    IMMEDIATE = 2


class LogicAnalyzerFSM(Elaboratable):
    """
    A module containing the state machine for a LogicAnalyzerCore. Primarily
    responsible for controlling the write port of the Logic Analyzer's sample
    memory in each trigger mode (immediate, incremental, single-shot).
    """

    def __init__(self, sample_depth, base_addr, interface):
        self._sample_depth = sample_depth

        # Outputs to rest of Logic Analyzer
        self.trigger = Signal(1)
        self.write_enable = Signal(1)

        # Outputs from FSM, inputs from IOCore
        self.state = Signal(States)
        self.read_pointer = Signal(range(self._sample_depth))
        self.write_pointer = Signal(range(self._sample_depth))
        inputs = [
            self.state,
            self.read_pointer,
            self.write_pointer,
        ]

        # Inputs to FSM, outputs from IOCore
        self.trigger_location = Signal(range(self._sample_depth))
        self.trigger_mode = Signal(TriggerModes)
        self.request_start = Signal()
        self.request_stop = Signal()
        outputs = [
            self.trigger_location,
            self.trigger_mode,
            self.request_start,
            self.request_stop,
        ]

        self.registers = IOCore(inputs, outputs)
        self.registers.base_addr = base_addr
        self.registers.interface = interface

        # Bus Input/Output
        self.bus_i = self.registers.bus_i
        self.bus_o = self.registers.bus_o

    @property
    def max_addr(self):
        return self.registers.max_addr

    def elaborate(self, platform):
        m = Module()

        m.submodules.registers = self.registers

        sample_depth = self._sample_depth
        request_start = self.request_start
        request_stop = self.request_stop
        trigger_mode = self.trigger_mode
        trigger_location = self.trigger_location
        state = self.state
        write_enable = self.write_enable
        write_pointer = self.write_pointer
        read_pointer = self.read_pointer

        prev_request_start = Signal().like(request_start)
        prev_request_stop = Signal().like(request_stop)

        # Compute next_write_pointer as write_pointer + 1 % sample_depth
        next_write_pointer = Signal().like(write_pointer)
        with m.If(write_pointer == self._sample_depth - 1):
            m.d.comb += next_write_pointer.eq(0)

        with m.Else():
            m.d.comb += next_write_pointer.eq(write_pointer + 1)

        # Rising edge detection for start/stop requests
        m.d.sync += prev_request_start.eq(request_start)
        m.d.sync += prev_request_stop.eq(request_stop)

        with m.If(state == States.IDLE):
            m.d.sync += write_pointer.eq(0)
            m.d.sync += read_pointer.eq(0)
            m.d.sync += write_enable.eq(0)

            with m.If((request_start) & (~prev_request_start)):
                with m.If(trigger_mode == TriggerModes.IMMEDIATE):
                    m.d.sync += state.eq(States.CAPTURING)
                    m.d.sync += write_enable.eq(1)

                with m.Elif(trigger_mode == TriggerModes.INCREMENTAL):
                    m.d.sync += state.eq(States.CAPTURING)
                    m.d.sync += write_enable.eq(1)

                with m.Elif(trigger_mode == TriggerModes.SINGLE_SHOT):
                    with m.If(trigger_location == 0):
                        m.d.sync += state.eq(States.IN_POSITION)

                    with m.Else():
                        m.d.sync += state.eq(States.MOVE_TO_POSITION)

                    m.d.sync += write_enable.eq(1)

        with m.Elif(state == States.MOVE_TO_POSITION):
            m.d.sync += write_pointer.eq(next_write_pointer)

            with m.If(write_pointer == trigger_location - 1):
                with m.If(self.trigger):
                    m.d.sync += state.eq(States.CAPTURING)

                with m.Else():
                    m.d.sync += state.eq(States.IN_POSITION)

        with m.Elif(state == States.IN_POSITION):
            m.d.sync += write_pointer.eq(next_write_pointer)

            with m.If(self.trigger):
                m.d.sync += state.eq(States.CAPTURING)

                # kind of horrible, i'll get rid of this later...
                with m.If(write_pointer > trigger_location):
                    m.d.sync += read_pointer.eq(write_pointer - trigger_location)
                with m.Else():
                    m.d.sync += read_pointer.eq(
                        write_pointer - trigger_location + sample_depth
                    )

                # ok that's all for horrible

        with m.If(state == States.CAPTURING):
            # Non- incremental modes
            with m.If(trigger_mode != TriggerModes.INCREMENTAL):
                with m.If(next_write_pointer == read_pointer):
                    m.d.sync += write_enable.eq(0)
                    m.d.sync += state.eq(States.CAPTURED)

                with m.Else():
                    m.d.sync += write_pointer.eq(next_write_pointer)

            # Incremental mode
            with m.Else():
                with m.If(self.trigger):
                    with m.If(next_write_pointer == read_pointer):
                        m.d.sync += write_enable.eq(0)
                        m.d.sync += state.eq(States.CAPTURED)

                    with m.Else():
                        m.d.sync += write_pointer.eq(next_write_pointer)

        # Regardless of trigger mode, go back to IDLE if request_stop is pulsed
        with m.If((request_stop) & (~prev_request_stop)):
            m.d.sync += state.eq(States.IDLE)

        return m

    def stop_capture(self):
        # If core is not in IDLE state, request that it return to IDLE
        state = self.registers.get_probe("state")
        if state != States.IDLE:
            self.registers.set_probe("request_start", 0)
            self.registers.set_probe("request_stop", 0)
            self.registers.set_probe("request_stop", 1)
            self.registers.set_probe("request_stop", 0)

            if self.registers.get_probe("state") != States.IDLE:
                raise ValueError("Logic analyzer did not reset to IDLE state.")

    def start_capture(self):
        # Send a start request to the state machine
        self.registers.set_probe("request_start", 0)
        self.registers.set_probe("request_start", 1)
        self.registers.set_probe("request_start", 0)

    def wait_for_capture(self):
        # Poll the state machine, and wait for the capture to complete
        while self.registers.get_probe("state") != States.CAPTURED:
            pass

    def read_register(self, name):
        return self.registers.get_probe(name)

    def write_register(self, name, value):
        return self.registers.set_probe(name, value)
