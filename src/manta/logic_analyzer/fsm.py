from amaranth import *
from math import ceil, log2
from ..io_core import IOCore


class LogicAnalyzerFSM(Elaboratable):
    """ """

    def __init__(self, config, base_addr, interface):
        self.config = config
        self.states = {
            "IDLE": 0,
            "MOVE_TO_POSITION": 1,
            "IN_POSITION": 2,
            "CAPTURING": 3,
            "CAPTURED": 4,
        }

        self.trigger_modes = {"SINGLE_SHOT": 0, "INCREMENTAL": 1, "IMMEDIATE": 2}

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

        next_state = Signal().like(state)
        next_read_pointer = Signal().like(read_pointer)
        latch_read_pointer = Signal().like(read_pointer)
        next_write_pointer = Signal().like(write_pointer)

        # COMBINATIONAL SHIT
        with m.If(trigger_mode == self.trigger_modes["SINGLE_SHOT"]):
            with m.If(state == self.states["IDLE"]):
                m.d.comb += write_enable.eq(0)
                m.d.comb += write_pointer.eq(0)
                m.d.comb += read_pointer.eq(0)
                m.d.comb += next_state.eq(self.states["IDLE"])

                # Rising edge of request_start beings the capture:
                with m.If((request_start) & (~prev_request_start)):
                    m.d.comb += write_enable.eq(1)
                    # Go straight to IN_POSITION if trigger_location == 0
                    with m.If(trigger_location == 0):
                        m.d.comb += next_state.eq(self.states["IN_POSITION"])

                    # Otherwise go to MOVE_TO_POSITION
                    with m.Else():
                        m.d.comb += next_state.eq(self.states["MOVE_TO_POSITION"])

            with m.Elif(state == self.states["MOVE_TO_POSITION"]):
                m.d.comb += write_enable.eq(1)
                m.d.comb += write_pointer.eq(next_write_pointer)
                m.d.comb += read_pointer.eq(0)
                m.d.comb += next_state.eq(self.states["MOVE_TO_POSITION"])

                with m.If(write_pointer == trigger_location - 1):
                    with m.If(self.trigger):
                        m.d.comb += next_state.eq(self.states["CAPTURING"])

                    with m.Else():
                        m.d.comb += next_state.eq(self.states["IN_POSITION"])

            with m.Elif(state == self.states["IN_POSITION"]):
                m.d.comb += write_enable.eq(1)
                m.d.comb += write_pointer.eq(next_write_pointer)
                m.d.comb += next_state.eq(self.states["IN_POSITION"])

                with m.If(self.trigger):
                    m.d.comb += next_state.eq(self.states["CAPTURING"])
                    m.d.comb += read_pointer.eq(latch_read_pointer)

                with m.Else():
                    m.d.comb += read_pointer.eq(next_read_pointer)

            with m.Elif(state == self.states["CAPTURING"]):
                m.d.comb += write_enable.eq(1)
                m.d.comb += read_pointer.eq(latch_read_pointer)
                m.d.comb += next_state.eq(self.states["CAPTURING"])

                with m.If(next_write_pointer == read_pointer):
                    m.d.comb += write_enable.eq(0)
                    m.d.comb += next_state.eq(self.states["CAPTURED"])

                with m.Else():
                    m.d.comb += write_pointer.eq(next_write_pointer)

            with m.Elif(state == self.states["CAPTURED"]):
                m.d.comb += next_state.eq(self.states["CAPTURED"])
                m.d.comb += read_pointer.eq(latch_read_pointer)
                m.d.comb += write_enable.eq(0)
                # m.d.comb += read_pointer.eq(read_pointer)
                # m.d.comb += write_pointer.eq(write_pointer)

        with m.If(self.r.trigger_mode == self.trigger_modes["IMMEDIATE"]):
            pass

        with m.If(self.r.trigger_mode == self.trigger_modes["INCREMENTAL"]):
            pass

        # Regardless of trigger mode, go back to IDLE if request_stop is pulsed
        with m.If((request_stop) & (~prev_request_stop)):
            m.d.comb += next_state.eq(self.states["IDLE"])

        # SEQUENTIAL SHIT

        # Rising edge detection for start/stop requests
        m.d.sync += prev_request_start.eq(request_start)
        m.d.sync += prev_request_stop.eq(request_stop)

        # Copy next into current
        m.d.sync += state.eq(next_state)
        m.d.sync += next_write_pointer.eq((write_pointer + 1) % sample_depth)
        m.d.sync += next_read_pointer.eq((read_pointer + 1) % sample_depth)
        m.d.sync += latch_read_pointer.eq(read_pointer)

        return m

        #### OLD STUFF FOR REFERENCE ####

        # with m.If(self.r.state == self.states["IDLE"]):
        #     m.d.sync += self.r.write_pointer.eq(0)
        #     m.d.sync += self.r.read_pointer.eq(0)
        #     m.d.sync += self.write_enable.eq(0)

        #     with m.If((self.r.request_start) & (~prev_request_start)):
        #         m.d.sync += self.write_enable.eq(1)
        #         with m.If(self.r.trigger_mode == self.trigger_modes["IMMEDIATE"]):
        #             m.d.sync += self.r.state.eq(self.states["CAPTURING"])
        #             m.d.sync += self.r.write_pointer.eq(self.r.write_pointer + 1)

        #         with m.Else():
        #             with m.If(self.r.trigger_location == 0):
        #                 m.d.sync += self.r.state.eq(self.states["IN_POSITION"])

        #             with m.Else():
        #                 m.d.sync += self.r.state.eq(self.states["MOVE_TO_POSITION"])

        #         # m.d.sync += self.r.state.eq(self.states["MOVE_TO_POSITION"])

        # with m.Elif(self.r.state == self.states["MOVE_TO_POSITION"]):
        #     m.d.sync += self.r.write_pointer.eq(self.r.write_pointer + 1)

        #     with m.If(self.r.write_pointer == self.r.trigger_location):
        #         with m.If(self.trigger):
        #             m.d.sync += self.r.state.eq(self.states["CAPTURING"])

        #         with m.Else():
        #             m.d.sync += self.r.state.eq(self.states["IN_POSITION"])
        #             self.increment_mod_sample_depth(m, self.r.read_pointer)

        # with m.Elif(self.r.state == self.states["IN_POSITION"]):
        #     self.increment_mod_sample_depth(m, self.r.write_pointer)

        #     with m.If(self.trigger):
        #         m.d.sync += self.r.state.eq(self.states["CAPTURING"])

        #     with m.Else():
        #         self.increment_mod_sample_depth(m, self.r.read_pointer)

        # with m.Elif(self.r.state == self.states["CAPTURING"]):
        #     with m.If(self.r.write_pointer == self.r.read_pointer):
        #         m.d.sync += self.write_enable.eq(0)
        #         m.d.sync += self.r.state.eq(self.states["CAPTURED"])

        #     with m.Else():
        #         self.increment_mod_sample_depth(m, self.r.write_pointer)

        # with m.If((self.r.request_stop) & (~prev_request_stop)):
        #     m.d.sync += self.r.state.eq(self.states["IDLE"])
