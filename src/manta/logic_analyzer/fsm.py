from amaranth import *
from amaranth.lib.enum import IntEnum
from math import ceil, log2
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

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.trigger = Signal(1)
        self.write_enable = Signal(1)

        register_config = {
            "inputs": {
                "state": 4,
                "read_pointer": ceil(log2(self.config["sample_depth"])),
                "write_pointer": ceil(log2(self.config["sample_depth"])),
            },
            "outputs": {
                "trigger_location": ceil(log2(self.config["sample_depth"])),
                "trigger_mode": 2,
                "request_start": 1,
                "request_stop": 1,
            },
        }

        self.r = IOCore(register_config, base_addr, interface)

        # Bus Input/Output
        self.bus_i = self.r.bus_i
        self.bus_o = self.r.bus_o

    def get_max_addr(self):
        """
        Return the maximum addresses in memory used by the core. The address space used
        by the core extends from `base_addr` to the number returned by this function.
        """
        return self.r.get_max_addr()

    def increment_mod_sample_depth(self, m, signal):
        # m.d.sync += signal.eq((signal + 1) % self.config["sample_depth"])

        with m.If(signal == self.config["sample_depth"] - 1):
            m.d.sync += signal.eq(0)

        with m.Else():
            m.d.sync += signal.eq(signal + 1)

    def elaborate(self, platform):
        m = Module()

        m.submodules.registers = self.r

        sample_depth = self.config["sample_depth"]
        request_start = self.r.request_start
        request_stop = self.r.request_stop
        trigger_mode = self.r.trigger_mode
        trigger_location = self.r.trigger_location
        state = self.r.state
        write_enable = self.write_enable
        write_pointer = self.r.write_pointer
        read_pointer = self.r.read_pointer

        prev_request_start = Signal(1)
        prev_request_stop = Signal(1)

        next_write_pointer = Signal().like(write_pointer)

        m.d.comb += next_write_pointer.eq((write_pointer + 1) % sample_depth)

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
