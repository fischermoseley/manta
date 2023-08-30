from ..utils import *

from datetime import datetime
from pkg_resources import get_distribution
import math
import os

class LogicAnalyzerCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # Warn if unrecognized options have been given
        valid_options = ["type", "sample_depth", "probes", "triggers", "trigger_loc", "trigger_mode"]
        for option in config:
            if option not in valid_options:
                print(f"Warning: Ignoring unrecognized option '{option}' in Logic Analyzer core '{self.name}'")

        # Load sample depth
        assert "sample_depth" in config, \
            "Sample depth not found for Logic Analyzer core {self.name}."

        assert isinstance(config["sample_depth"], int), \
            "Sample depth must be an integer."

        self.sample_depth = config["sample_depth"]

        # Add probes
        assert "probes" in config, "No probe definitions found."
        assert len(config["probes"]) > 0, "Must specify at least one probe."

        for probe_name, probe_width in config["probes"].items():
            assert probe_width > 0, f"Probe {probe_name} is of invalid width - it must be of at least width one."

        self.probes = config["probes"]

        # Add triggers
        assert "triggers" in config, "No triggers found."
        assert len(config["triggers"]) > 0, "Must specify at least one trigger."
        self.triggers = config["triggers"]

        # Add trigger location
        self.trigger_loc = self.sample_depth // 2
        if "trigger_loc" in config:
            assert isinstance(config["trigger_loc"], int), \
                "Trigger location must be an integer."

            assert config["trigger_loc"] >= 0, \
                "Trigger location cannot be negative."

            assert config["trigger_loc"] <= self.sample_depth, \
                "Trigger location cannot exceed sample depth."

            self.trigger_loc = config["trigger_loc"]

        # Add trigger mode
        self.SINGLE_SHOT = 0
        self.INCREMENTAL = 1
        self.IMMEDIATE = 2

        self.trigger_mode = self.SINGLE_SHOT
        if "trigger_mode" in config:
            assert config["trigger_mode"] in ["single_shot", "incremental", "immediate"], \
                "Unrecognized trigger mode provided."

            if config["trigger_mode"] == "single_shot":
                self.trigger_mode = self.SINGLE_SHOT

            elif config["trigger_mode"] == "incremental":
                self.trigger_mode = self.INCREMENTAL

            elif config["trigger_mode"] == "immediate":
                self.trigger_mode = self.IMMEDIATE

        # compute base addresses
        self.fsm_base_addr = self.base_addr
        self.trigger_block_base_addr = self.fsm_base_addr + 7

        self.total_probe_width = sum(self.probes.values())
        self.n_brams = math.ceil(self.total_probe_width / 16)
        self.block_memory_base_addr = self.trigger_block_base_addr + (2*len(self.probes))
        self.max_addr = self.block_memory_base_addr + (self.n_brams * self.sample_depth)

        # build out self register map:
        #   these are also defined in logic_analyzer_fsm_registers.v, and should match
        self.state_reg_addr = self.base_addr
        self.trigger_mode_reg_addr = self.base_addr + 1
        self.trigger_loc_reg_addr = self.base_addr + 2
        self.request_start_reg_addr = self.base_addr + 3
        self.request_stop_reg_addr = self.base_addr + 4
        self.read_pointer_reg_addr = self.base_addr + 5
        self.write_pointer_reg_addr = self.base_addr + 6

        self.IDLE = 0
        self.MOVE_TO_POSITION = 1
        self.IN_POSITION = 2
        self.CAPTURING = 3
        self.CAPTURED = 4

    def hdl_inst(self):
        la_inst = VerilogManipulator("la_core/logic_analyzer_inst_tmpl.v")

        # add module name to instantiation
        la_inst.sub(self.name, "/* INST_NAME */")

        # add net connections to instantiation
        conns = la_inst.net_conn(self.probes, trailing_comma=True)
        la_inst.sub(conns, "/* NET_CONNS */")
        return la_inst.get_hdl()

    def gen_trigger_block_def(self):
        trigger_block = VerilogManipulator("la_core/trigger_block_def_tmpl.v")

        # add probe ports to module declaration
        # these ports belong to the logic analyzer, but
        # need to be included in the trigger_block module declaration
        probe_ports = trigger_block.net_dec(self.probes, "input wire", trailing_comma=True)
        trigger_block.sub(probe_ports, "/* PROBE_PORTS */")


        # add trigger cores to module definition
        # these are instances of the trigger module, of which one gets wired
        # into each probe
        trigger_module_insts = []
        for name, width in self.probes.items():
            trig_inst = VerilogManipulator("la_core/trigger_block_inst_tmpl.v")
            trig_inst.sub(width, "/* INPUT_WIDTH */")
            trig_inst.sub(f"{name}_trigger", "/* NAME */")

            trig_inst.sub(f"reg [3:0] {name}_op = 0;", "/* OP_DEC */")
            trig_inst.sub(f"reg {name}_trig;", "/* TRIG_DEC */")

            if width == 1:
                trig_inst.sub(f"reg {name}_arg = 0;", "/* ARG_DEC */")

            else:
                trig_inst.sub(f"reg [{width-1}:0] {name}_arg = 0;", "/* ARG_DEC */")

            trig_inst.sub(name, "/* PROBE */")
            trig_inst.sub(f"{name}_op", "/* OP */")
            trig_inst.sub(f"{name}_arg", "/* ARG */")
            trig_inst.sub(f"{name}_trig", "/* TRIG */")

            trigger_module_insts.append(trig_inst.get_hdl())

        trigger_module_insts = "\n".join(trigger_module_insts)
        trigger_block.sub(trigger_module_insts, "/* TRIGGER_MODULE_INSTS */")

        # add combined individual triggers
        cit = [f"{name}_trig" for name in self.probes]
        cit = " || ".join(cit)
        cit = f"assign trig = {cit};"
        trigger_block.sub(cit, " /* COMBINE_INDIV_TRIGGERS */")

        # add read and write block case statement bodies
        rcsb = "" # read case statement body
        wcsb = "" # write case statement body
        addr = 0
        for i, name in enumerate(self.probes):
            addr = 2 * i
            rcsb += f"BASE_ADDR + {addr}: data_o <= {name}_op;\n"
            wcsb += f"BASE_ADDR + {addr}: {name}_op <= data_i;\n"

            addr = (2 * i) + 1
            rcsb += f"BASE_ADDR + {addr}: data_o <= {name}_arg;\n"
            wcsb += f"BASE_ADDR + {addr}: {name}_arg <= data_i;\n"

        rcsb = rcsb.strip()
        wcsb = wcsb.strip()

        trigger_block.sub(rcsb, "/* READ_CASE_STATEMENT_BODY */")
        trigger_block.sub(wcsb, "/* WRITE_CASE_STATEMENT_BODY */")
        trigger_block.sub(self.trigger_block_base_addr + addr + 1, "/* MAX_ADDR */")

        return trigger_block.get_hdl()

    def gen_logic_analyzer_def(self):
        la = VerilogManipulator("la_core/logic_analyzer_def_tmpl.v")

        # add top level probe ports to module declaration
        ports = la.net_dec(self.probes, "input wire", trailing_comma=True)
        la.sub(ports, "/* TOP_LEVEL_PROBE_PORTS */")

        # assign base addresses to the FSM, trigger block, and sample mem
        la.sub(self.fsm_base_addr, "/* FSM_BASE_ADDR */")
        la.sub(self.trigger_block_base_addr, "/* TRIGGER_BLOCK_BASE_ADDR */")
        la.sub(self.block_memory_base_addr, "/* BLOCK_MEMORY_BASE_ADDR */")

        # set sample depth
        la.sub(self.sample_depth, "/* SAMPLE_DEPTH */")

        # set probe ports for the trigger block and sample mem
        probe_ports = la.net_conn(self.probes, trailing_comma=True)
        la.sub(probe_ports, "/* TRIGGER_BLOCK_PROBE_PORTS */")

        la.sub(self.total_probe_width, "/* TOTAL_PROBE_WIDTH */")

        # concatenate the probes together to make one big register,
        #   but do so such that the first probe in the config file
        #   is at the least-significant position in that big register.
        #
        #   this makes part-selecting out from the memory easier to
        #   implement in python, and because verilog and python conventions
        #   are different, we would have had to reverse it somwehere anyway
        probes_concat = list(self.probes.keys())[::-1]
        probes_concat = '{' + ', '.join(probes_concat) + '}'
        la.sub(probes_concat, "/* PROBES_CONCAT */")

        return la.get_hdl()

    def hdl_def(self):
        # Return an autogenerated verilog module definition for the core.
        # load source files
        hdl = self.gen_logic_analyzer_def() + "\n"
        hdl += VerilogManipulator("la_core/logic_analyzer_controller.v").get_hdl() + "\n"
        hdl += VerilogManipulator("la_core/logic_analyzer_fsm_registers.v").get_hdl() + "\n"
        hdl += VerilogManipulator("block_mem_core/block_memory.v").get_hdl() + "\n"
        hdl += VerilogManipulator("block_mem_core/dual_port_bram.v").get_hdl() + "\n"
        hdl += self.gen_trigger_block_def() + "\n"
        hdl += VerilogManipulator("la_core/trigger.v").get_hdl() + "\n"

        return hdl

    def hdl_top_level_ports(self):
        # the probes that we want as ports on the top-level manta module
        ports = []
        for name, width in self.probes.items():
            if width == 1:
                ports.append(f"input wire {name}")

            else:
                ports.append(f"input wire [{width-1}:0] {name}")
        return ports
        #return VerilogManipulator().net_dec(self.probes, "input wire")

    def set_trigger_conditions(self):

        operations = {
            "DISABLE" : 0,
            "RISING" : 1,
            "FALLING" : 2,
            "CHANGING" : 3,
            "GT" : 4,
            "LT" : 5,
            "GEQ" : 6,
            "LEQ" : 7,
            "EQ" : 8,
            "NEQ" : 9
        }

        ops_with_no_args = ["DISABLE", "RISING" , "FALLING", "CHANGING"]

        # reset all the other triggers
        for addr in range(self.trigger_block_base_addr, self.block_memory_base_addr):
            self.interface.write(addr, 0)

        for trigger in self.triggers:
            # determine if the trigger is good

            # most triggers will have 3 parts - the trigger, the operation, and the argument
            # this is true unless the argument is RISING, FALLING, or CHANGING

            statement = trigger.split(' ')
            if len(statement) == 2:
                assert statement[1] in ops_with_no_args, "Invalid operation in trigger statement."
                probe_name, op = statement

                op_register = 2*(list(self.probes.keys()).index(probe_name)) + self.trigger_block_base_addr

                self.interface.write(op_register, operations[op])

            else:
                assert len(statement) == 3, "Missing information in trigger statement."
                probe_name, op, arg = statement

                op_register = 2*(list(self.probes.keys()).index(probe_name)) + self.trigger_block_base_addr
                arg_register = op_register + 1

                self.interface.write(op_register, operations[op])
                self.interface.write(arg_register, int(arg))



    # functions for actually using the core:
    def capture(self):
        # Check state - if it's in anything other than IDLE,
        # request to stop the existing capture

        print(" -> Resetting core...")
        state = self.interface.read(self.state_reg_addr)
        if state != self.IDLE:
            self.interface.write(self.request_stop_reg_addr, 0)
            self.interface.write(self.request_stop_reg_addr, 1)
            self.interface.write(self.request_stop_reg_addr, 0)

            state = self.interface.read(self.state_reg_addr)
            assert state == self.IDLE, "Logic analyzer did not reset to correct state when requested to."

        # Configure trigger conditions
        print(" -> Set trigger conditions...")
        self.set_trigger_conditions()

        # Configure the trigger_mode
        print(" -> Setting trigger mode")
        self.interface.write(self.trigger_mode_reg_addr, self.trigger_mode)

        # Configure the trigger_loc
        print(" -> Setting trigger location...")
        self.interface.write(self.trigger_loc_reg_addr, self.trigger_loc)

        # Start the capture by pulsing request_start
        print(" -> Starting capture...")
        self.interface.write(self.request_start_reg_addr, 1)
        self.interface.write(self.request_start_reg_addr, 0)

        # Wait for core to finish capturing data
        print(" -> Waiting for capture to complete...")
        state = self.interface.read(self.state_reg_addr)
        while(state != self.CAPTURED):
            state = self.interface.read(self.state_reg_addr)

        # Read out contents from memory
        print(" -> Reading sample memory contents...")
        addrs = list(range(self.block_memory_base_addr, self.max_addr))
        block_mem_contents = self.interface.read(addrs)

        # Revolve BRAM contents around so the data pointed to by the read_pointer
        # is at the beginning
        print(" -> Reading read_pointer and revolving memory...")
        read_pointer = self.interface.read(self.read_pointer_reg_addr)

        # when the total probe width is >16 bits and multiple BRAMs are used,
        # then a single sample is stored across multiple locations in memory,
        # so we must combine the data from n_brams addresses to get the value
        # of the sample at that time

        # convert the sample number at read_pointer to memory address
        read_address = self.n_brams * read_pointer
        sample_mem = block_mem_contents[read_address:] + block_mem_contents[:read_address]

        # split sample memory into chunks of size n_brams
        chunks = [sample_mem[i: i + self.n_brams] for i in range(0, len(sample_mem), self.n_brams)]

        # concat them in little-endian order (ie, chunk[0] is LSB)
        concat = lambda x: int( ''.join([f'{i:016b}' for i in x[::-1]]), 2)
        return [concat(c) for c in chunks]


    def export_vcd(self, capture_data, path):
        from vcd import VCDWriter
        vcd_file = open(path, "w")

        # Use the same datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")

        with VCDWriter(vcd_file, '10 ns', timestamp, "manta") as writer:

            # each probe has a name, width, and writer associated with it
            signals = []
            for name, width in self.probes.items():
                signal = {
                    "name" : name,
                    "width" : width,
                    "data" : self.part_select_capture_data(capture_data, name),
                    "var": writer.register_var("manta", name, "wire", size=width)
                }
                signals.append(signal)

            clock = writer.register_var("manta", "clk", "wire", size=1)
            trigger = writer.register_var("manta", "trigger", "wire", size=1)

            # add the data to each probe in the vcd file
            for timestamp in range(0, 2*len(capture_data)):

                # run the clock
                writer.change(clock, timestamp, timestamp % 2 == 0)

                # set the trigger
                triggered = (timestamp // 2) >= self.trigger_loc
                writer.change(trigger, timestamp, triggered)

                # add other signals
                for signal in signals:
                    var = signal["var"]
                    sample = signal["data"][timestamp // 2]

                    writer.change(var, timestamp, sample)

        vcd_file.close()

    def export_mem(self, capture_data, path):
        with open(path, "w") as f:
            # a wee bit of cursed string formatting, but just
            # outputs each sample as binary, padded to a fixed length
            w = self.total_probe_width
            f.writelines([f'{s:0{w}b}\n' for s in capture_data])

    def export_playback_module(self, path):
        playback = VerilogManipulator("la_core/logic_analyzer_playback_tmpl.v")

        module_name = f"{self.name}_playback"
        playback.sub(module_name, "/* MODULE_NAME */")

        version = "v" + get_distribution('mantaray').version
        playback.sub(version, "/* VERSION */")

        timestamp = datetime.now().strftime("%d %b %Y at %H:%M:%S")
        playback.sub(timestamp, "/* TIMESTAMP */")

        user = os.environ.get("USER", os.environ.get("USERNAME"))
        playback.sub(user, "/* USER */")

        ports = [f".{name}({name})" for name in self.probes.keys()]
        ports = ",\n".join(ports)
        playback.sub(ports, "/* PORTS */")

        playback.sub(self.sample_depth, "/* SAMPLE_DEPTH */")
        playback.sub(self.total_probe_width, "/* TOTAL_PROBE_WIDTH */")

        # see the note in generate_logic_analyzer_def about why we do this
        probes_concat = list(self.probes.keys())[::-1]
        probes_concat = '{' + ', '.join(probes_concat) + '}'
        playback.sub(probes_concat, "/* PROBES_CONCAT */")


        probe_dec = playback.net_dec(self.probes, "output reg")
        playback.sub(probe_dec, "/* PROBE_DEC */")

        with open(path, "w") as f:
            f.write(playback.get_hdl())


    def part_select_capture_data(self, capture_data, probe_name):
        """Given the name of the probe, part-select the appropriate bits of capture data,
        and return as an integer. Accepts capture_data as an integer or a list of integers."""

        # sum up the widths of the probes below this one
        lower = 0
        for name, width in self.probes.items():
            if name == probe_name:
                break

            lower += width

        upper = lower + (self.probes[probe_name] - 1)

        # define the part select
        mask = 2 ** (upper - lower + 1) - 1
        part_select = lambda x: (x >> lower) & mask

        # apply the part_select function depending on type
        if isinstance(capture_data, int):
            return part_select(capture_data)

        elif isinstance(capture_data, list):
            for i in capture_data:
                assert isinstance(i, int), "Can only part select on integers and list of integers."

            return [part_select(sample) for sample in capture_data]

        else:
            raise ValueError("Can only part select on integers and lists of integers.")
