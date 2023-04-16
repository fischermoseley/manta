import pkgutil
import math
from sys import argv
import os
from datetime import datetime

version = "v0.0.0"

class VerilogManipulator:
    def __init__(self, filepath=None):
        if filepath is not None:
            self.hdl = pkgutil.get_data(__name__, filepath).decode()

            # scrub any default_nettype or timescale directives from the source
            self.hdl = self.hdl.replace("`default_nettype none", "")
            self.hdl = self.hdl.replace("`default_nettype wire", "")
            self.hdl = self.hdl.replace("`timescale 1ns/1ps", "")
            self.hdl = self.hdl.strip()

            # python tries to be cute and automatically convert
            # line endings on Windows, but Manta's source comes
            # with (and injects) UNIX line endings, so Python
            # ends up adding way too many line breaks, so we just
            # undo anything it's done when we load the file
            self.hdl = self.hdl.replace("\r\n", "\n")

        else:
            self.hdl = None

    def sub(self, replace, find):
        # sometimes we have integer inputs, want to accomodate
        if isinstance(replace, str):
            replace_str = replace

        elif isinstance(replace, int):
            replace_str = str(replace)

        else:
            raise ValueError("Only string and integer arguments supported.")


        # if the string being subbed in isn't multiline, just
        # find-and-replace like normal:
        if "\n" not in replace_str:
            self.hdl = self.hdl.replace(find, replace_str)

        # if the string being substituted in is multiline,
        # make sure the replace text gets put at the same
        # indentation level by adding whitespace to left
        # of the line.
        else:
            for line in self.hdl.split("\n"):
                if find in line:
                    # get whitespace that's on the left side of the line
                    whitespace = line.rstrip().replace(line.lstrip(), "")

                    # add it to every line, except the first
                    replace_as_lines = replace_str.split("\n")
                    replace_with_whitespace = f"\n{whitespace}".join(replace_as_lines)

                    # replace the first occurance in the HDL with it
                    self.hdl = self.hdl.replace(find, replace_with_whitespace, 1)

    def get_hdl(self):
        return self.hdl

    def net_dec(self, nets, net_type, trailing_comma = False):
        """Takes a dictonary of nets in the format {probe: width}, and generates
        the net declarations that would go in a Verilog module definition.

        For example, calling net_dec({foo : 1, bar : 4}, "input wire") would produce:

        input wire foo,
        input [3:0] wire bar

        Which you'd then slap into your module declaration, along with all the other
        inputs and outputs the module needs."""

        dec = []
        for name, width in nets.items():
            if width == 1:
                dec.append(f"{net_type} {name}")

            else:
                dec.append(f"{net_type} [{width-1}:0] {name}")

        dec = ",\n".join(dec)
        dec = dec + "," if trailing_comma else dec
        return dec

    def net_conn(self, nets, trailing_comma = False):
        """Takes a dictionary of nets in the format {probe: width}, and generates
        the net connections that would go in the Verilog module instantiation.

        For example, calling net_conn({foo: 1, bar: 4}) would produce:

        .foo(foo),
        .bar(bar)

        Which you'd then slap into your module instantiation, along with all the other
        module inputs and outputs that get connected elsewhere."""


        conn = [f".{name}({name})" for name in nets]
        conn = ",\n".join(conn)
        conn = conn + "," if trailing_comma else conn

        return conn

class UARTInterface:
    def __init__(self, config):
        # Obtain port. Try to automatically detect port if "auto" is specified
        assert "port" in config, "No serial port provided to UART core."
        self.port = config["port"]

        # Check that clock frequency is provided and positive
        assert "clock_freq" in config, "Clock frequency not provided to UART core."
        assert config["clock_freq"] > 0, "Clock frequency must be positive."
        self.clock_freq = config["clock_freq"]

        # Check that baudrate is provided and positive
        assert "baudrate" in config, "Baudrate not provided to UART core."
        assert config["baudrate"] > 0, "Baudrate must be positive."
        self.baudrate = config["baudrate"]

        # Confirm core clock is sufficiently fast
        clocks_per_baud = self.clock_freq // self.baudrate
        assert clocks_per_baud >= 2
        self.clocks_per_baud = clocks_per_baud

        # Confirm we can match baudrate suffeciently well
        actual_baudrate = self.clock_freq / clocks_per_baud
        baudrate_error = 100 * abs(actual_baudrate - self.baudrate) / self.baudrate
        assert (
            baudrate_error <= 5
        ), "Unable to match target baudrate - they differ by {baudrate_error}%"

        # Set chunk_size, which is the max amount of bytes that get dumped
        # to the OS driver at a time
        self.chunk_size = 256
        if "chunk size" in config:
            self.chunk_size = config["chunk size"]

        # Set verbosity
        self.verbose = False
        if "verbose" in config:
            self.verbose = config["verbose"]

    def open_port_if_not_alredy_open(self):
        if self.port == "auto":
            self.port = self.autodetect_port()

        if not hasattr(self, "ser"):
            import serial
            self.ser = serial.Serial(self.port, self.baudrate)

    def autodetect_port(self):
        # as far as I know the FT2232 is the only chip used on the icestick/digilent boards, so just look for that
        import serial.tools.list_ports

        recognized_devices = []
        for port in serial.tools.list_ports.comports():
            if (port.vid == 0x403) and (port.pid == 0x6010):
                recognized_devices.append(port)

        # board manufacturers seem to always make the 0th serial
        # interface on the FT2232 be for programming over JTAG,
        # and then the 1st to be for UART. as a result, we always
        # grab the device with the larger location

        rd = recognized_devices
        assert len(recognized_devices) == 2, f"Expected to see two serial ports for FT2232 device, but instead see {len(recognized_devices)}."
        assert rd[0].serial_number == rd[1].serial_number, "Serial numbers should be the same on both FT2232 ports - probably somehow grabbed ports on two different devices."
        return rd[0].device if rd[0].location > rd[1].location else rd[1].device

    def decode_response(self, response):
        """Make sure reponse from FPGA has the correct format, and return data contained within if so."""
        assert response is not None, "No reponse received."

        response_str = response.decode('ascii')
        assert response_str[0] == 'M', "Bad message recieved, incorrect preamble."
        assert response_str[-1] == '\n', "Bad message received, incorrect EOL."
        assert response_str[-2] == '\r', "Bad message received, incorrect EOL."
        assert len(response_str) == 7, f"Wrong number of bytes received, expecting 7 but got {len(response)}."

        return int(response_str[1:5], 16)

    def read_register(self, addr):
        self.open_port_if_not_alredy_open()

        # request from the bus
        request = f"M{addr:04X}\r\n".encode('ascii')
        self.ser.write(request)

        # read and parse the response
        data = self.decode_response(self.ser.read(7))

        if self.verbose:
            print(f"read {data:04X} from {addr:04X}")

        return data

    def write_register(self, addr, data):
        self.open_port_if_not_alredy_open()

        # request from the bus
        request = f"M{addr:04X}{data:04X}\r\n".encode('ascii')
        self.ser.write(request)

        if self.verbose:
            print(f"wrote {data:04X} to {addr:04X}")

    def read_registers(self, addrs):
        assert isinstance(addrs, list), "Read addresses must be list of integers."
        assert all(isinstance(addr, int) for addr in addrs), "Read addresses must be list of integers."

        # send data in chunks because the reponses will fill up the OS's
        # input buffer in no time flat
        self.open_port_if_not_alredy_open()

        inbound_bytes = b""
        for i in range(0, len(addrs), self.chunk_size):
            addr_chunk = addrs[i:i+self.chunk_size]

            outbound_bytes = [f"M{addr:04X}\r\n".encode('ascii') for addr in addr_chunk]
            outbound_bytes = b"".join(outbound_bytes)

            self.ser.write(outbound_bytes)

            inbound_bytes += self.ser.read(len(outbound_bytes))

        data = []
        for i in range(0, len(inbound_bytes), 7):
            response = inbound_bytes[i:i+7]
            data = self.decode_response(response)

        return data

    def write_registers(self, addrs, datas):
        assert isinstance(addrs, list), "Write addresses must be list of integers."
        assert isinstance(datas, list), "Write data must be list of integers."
        assert all(isinstance(addr, int) for addr in addrs), "Write addresses must be list of integers."
        assert all(isinstance(data, int) for data in datas), "Write data must be list of integers."
        assert len(addrs) == len(datas), "Write addresses and write data must be of same length."

        # send data in chunks because the responses will fill up the OS's
        # input buffer in no time flat
        self.open_port_if_not_alredy_open()

        for i in range(0, len(addrs), self.chunk_size):
            addr_chunk = addrs[i:i+self.chunk_size]

            outbound_bytes = [f"M{addrs[i]:04X}{datas[i]:04X}\r\n" for i in range(len(addr_chunk))]
            outbound_bytes = [ob.encode('ascii') for ob in outbound_bytes]
            outbound_bytes = b"".join(outbound_bytes)

            self.ser.write(outbound_bytes)

    def hdl_top_level_ports(self):
        # this should return the probes that we want to connect to top-level, but like as a string of verilog

        return ["input wire rx", "output reg tx"]

    def rx_hdl_def(self):
        uart_rx_def = VerilogManipulator("rx_uart.v").get_hdl()
        bridge_rx_def = VerilogManipulator("bridge_rx.v").get_hdl()
        return uart_rx_def + '\n' + bridge_rx_def

    def tx_hdl_def(self):
        uart_tx_def = VerilogManipulator("uart_tx.v").get_hdl()
        bridge_tx_def = VerilogManipulator("bridge_tx.v").get_hdl()
        return bridge_tx_def + '\n' + uart_tx_def

    def rx_hdl_inst(self):
        rx = VerilogManipulator("uart_rx_bridge_rx_inst_templ.v")
        rx.sub(self.clocks_per_baud, "/* CLOCKS_PER_BAUD */")
        return rx.get_hdl()

    def tx_hdl_inst(self):
        tx = VerilogManipulator("uart_tx_bridge_tx_inst_templ.v")
        tx.sub(self.clocks_per_baud, "/* CLOCKS_PER_BAUD */")
        return tx.get_hdl()

class IOCoreProbe:
    def __init__(self, name, width, direction, base_addr, interface):
        self.name = name
        self.width = width
        self.direction = direction
        self.base_addr = base_addr
        self.interface = interface

    def set(self, data):
        # make sure that we're an output probe
        assert self.direction == "output", "Cannot set value of input port."

        # check that value is within range for the width of the probe
        assert isinstance(data, int), "Data must be an integer."
        if data > 0:
            assert data <= (2**self.width) - 1, f"Unsigned value too large for probe of width {self.width}"

        elif data < 0:
            assert data >= -(2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"
            assert data <= (2**(self.width-1))-1, f"Signed value too large for probe of width {self.width}"

        self.interface.write_register(self.base_addr, data)

    def get(self):
        return self.interface.read_register(self.base_addr)

class IOCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # make sure we have ports defined
        assert ('inputs' in config) or ('outputs' in config), "No input or output ports specified."

        # add input probes to core
        self.probes = []
        probe_base_addr = self.base_addr
        if 'inputs' in config:
           for name, width in config["inputs"].items():
                # make sure inputs are of reasonable width
                assert isinstance(width, int), f"Probe {name} must have integer width."
                assert width > 0, f"Probe {name} must have positive width."

                probe = IOCoreProbe(name, width, "input", probe_base_addr, self.interface)

                # add friendly name, so users can do Manta.my_io_core.my_probe.set() for example
                setattr(self, name, probe)
                self.probes.append(probe)

                self.max_addr = probe_base_addr
                probe_base_addr += 1

        # add output probes to core
        if 'outputs' in config:
            for name, width in config["outputs"].items():
                # make sure inputs are of reasonable width
                assert isinstance(width, int), f"Probe {name} must have integer width."
                assert width > 0, f"Probe {name} must have positive width."

                probe = IOCoreProbe(name, width, "output", probe_base_addr, self.interface)

                # add friendly name, so users can do Manta.my_io_core.my_probe.set() for example
                setattr(self, name, probe)
                self.probes.append(probe)

                self.max_addr = probe_base_addr
                probe_base_addr += 1


    def hdl_inst(self):
        inst = VerilogManipulator("io_core_inst_tmpl.v")
        inst.sub(self.name, "/* MODULE_NAME */")
        inst.sub(self.name + "_inst", "/* INST_NAME */")

        probes = {probe.name:probe.width for probe in self.probes}

        inst_ports = inst.net_conn(probes, trailing_comma=True)
        inst.sub(inst_ports, "/* INST_PORTS */")

        return inst.get_hdl()


    def hdl_def(self):
        io_core = VerilogManipulator("io_core_def_tmpl.v")
        io_core.sub(self.name, "/* MODULE_NAME */")
        io_core.sub(self.max_addr, "/* MAX_ADDR */")

        # generate declaration
        top_level_ports = ',\n'.join(self.hdl_top_level_ports())
        top_level_ports += ','
        io_core.sub(top_level_ports, "/* TOP_LEVEL_PORTS */")

        # generate memory handling
        rcsb = "" # read case statement body
        wcsb = "" # write case statement body
        for probe in self.probes:

            # add to read block
            if probe.width == 16:
                rcsb += f"{probe.base_addr}: rdata_o <= {probe.name};\n"

            else:
                rcsb += f"{probe.base_addr}: rdata_o <= {{{16-probe.width}'b0, {probe.name}}};\n"


            # if output, add to write block
            if probe.direction == "output":
                if probe.width == 1:
                    wcsb += f"{probe.base_addr}: {probe.name} <= wdata_i[0];\n"

                elif probe.width == 16:
                    wcsb += f"{probe.base_addr}: {probe.name} <= wdata_i;\n"

                else:
                    wcsb += f"{probe.base_addr}: {probe.name} <= wdata_i[{probe.width-1}:0];\n"

        # remove trailing newline
        rcsb = rcsb.rstrip()
        wcsb = wcsb.rstrip()

        io_core.sub(rcsb, "/* READ_CASE_STATEMENT_BODY */")
        io_core.sub(wcsb, "/* WRITE_CASE_STATEMENT_BODY */")

        return io_core.get_hdl()



    def hdl_top_level_ports(self):
        ports = []
        for probe in self.probes:
            net_type = "input wire " if probe.direction == "input" else "output reg "
            name_def = probe.name if probe.width == 1 else f"[{probe.width-1}:0] {probe.name}"
            ports.append(net_type + name_def)

        return ports

class LUTRAMCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        assert "size" in config, "Size not specified for LUT RAM core."
        assert config["size"] > 0, "LUT RAM must have positive size."
        assert isinstance(config["size"], int), "LUT RAM must have integer size."
        self.size = config["size"]

        self.max_addr = self.base_addr + self.size - 1

    def hdl_inst(self):
        inst = VerilogManipulator("lut_ram_inst_tmpl.v")
        inst.sub(self.size, "/* DEPTH */")
        inst.sub(self.name, "/* INST_NAME */")
        return inst.get_hdl()

    def hdl_def(self):
        return VerilogManipulator("lut_ram.v").get_hdl()

    def hdl_top_level_ports(self):
        # no top_level connections since this core just lives on the bus
        return ""

    def read(self, addr):
        return self.interface.read_register(addr + self.base_addr)

    def write(self, addr, data):
        return self.interface.write_register(addr + self.base_addr, data)

class LogicAnalyzerCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # load config
        assert (
            "sample_depth" in config
        ), "Sample depth not found for logic analyzer core."
        self.sample_depth = config["sample_depth"]

        assert "probes" in config, "No probe definitions found."
        assert len(config["probes"]) > 0, "Must specify at least one probe."

        for probe_name, probe_width in config["probes"].items():
            assert (
                probe_width > 0
            ), f"Probe {probe_name} is of invalid width - it must be of at least width one."

        self.probes = config["probes"]

        assert "triggers" in config, "No triggers found."
        assert len(config["triggers"]) > 0, "Must specify at least one trigger."
        self.triggers = config["triggers"]


        # compute base addresses
        self.fsm_base_addr = self.base_addr
        self.trigger_block_base_addr = self.fsm_base_addr + 6

        self.total_probe_width = sum(self.probes.values())
        n_brams = math.ceil(self.total_probe_width / 16)
        self.block_memory_base_addr = self.trigger_block_base_addr + (2*len(self.probes))
        self.max_addr = self.block_memory_base_addr + (n_brams * self.sample_depth)

        # build out self register map:
        #   these are also defined in logic_analyzer_fsm_registers.v, and should match
        self.state_reg_addr = self.base_addr
        self.trigger_loc_reg_addr = self.base_addr + 1
        self.current_loc_reg_addr = self.base_addr + 2
        self.request_start_reg_addr = self.base_addr + 3
        self.request_stop_reg_addr = self.base_addr + 4
        self.read_pointer_reg_addr = self.base_addr + 5

        self.IDLE = 0
        self.MOVE_TO_POSITION = 1
        self.IN_POSITION = 2
        self.CAPTURING = 3
        self.CAPTURED = 4

    def hdl_inst(self):
        la_inst = VerilogManipulator("logic_analyzer_inst_tmpl.v")

        # add module name to instantiation
        la_inst.sub(self.name, "/* INST_NAME */")

        # add net connections to instantiation
        conns = la_inst.net_conn(self.probes, trailing_comma=True)
        la_inst.sub(conns, "/* NET_CONNS */")
        return la_inst.get_hdl()

    def gen_trigger_block_def(self):
        trigger_block = VerilogManipulator("trigger_block_def_tmpl.v")

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
            trig_inst = VerilogManipulator("trigger_block_inst_tmpl.v")
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
            rcsb += f"BASE_ADDR + {addr}: rdata_o <= {name}_op;\n"
            wcsb += f"BASE_ADDR + {addr}: {name}_op <= wdata_i;\n"

            addr = (2 * i) + 1
            rcsb += f"BASE_ADDR + {addr}: rdata_o <= {name}_arg;\n"
            wcsb += f"BASE_ADDR + {addr}: {name}_arg <= wdata_i;\n"

        rcsb = rcsb.strip()
        wcsb = wcsb.strip()

        trigger_block.sub(rcsb, "/* READ_CASE_STATEMENT_BODY */")
        trigger_block.sub(wcsb, "/* WRITE_CASE_STATEMENT_BODY */")
        trigger_block.sub(addr, "/* MAX_ADDR */")

        return trigger_block.get_hdl()

    def gen_logic_analyzer_def(self):
        la = VerilogManipulator("logic_analyzer_def_tmpl.v")

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
        hdl += VerilogManipulator("logic_analyzer_controller.v").get_hdl() + "\n"
        hdl += VerilogManipulator("logic_analyzer_fsm_registers.v").get_hdl() + "\n"
        hdl += VerilogManipulator("block_memory.v").get_hdl() + "\n"
        hdl += VerilogManipulator("dual_port_bram.v").get_hdl() + "\n"
        hdl += self.gen_trigger_block_def() + "\n"
        hdl += VerilogManipulator("trigger.v").get_hdl() + "\n"

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



    # functions for actually using the core:
    def capture(self):
        # Check state - if it's in anything other than IDLE,
        # request to stop the existing capture
        print(" -> Resetting core...")
        state = self.interface.read_register(self.state_reg_addr)
        if state != self.IDLE:
            self.interface.write_register(self.request_stop_reg_addr, 0)
            self.interface.write_register(self.request_stop_reg_addr, 1)

            state = self.interface.read_register(self.state_reg_addr)
            assert state == self.IDLE, "Logic analyzer did not reset to correct state when requested to."

        # Configure trigger settings and positions - highkey don't really know how we're going to do this
        #   for now, let's just trigger on a changing value of the first probe
        print(" -> Configuring triggers...")
        self.interface.write_register(self.trigger_block_base_addr, 3)
        trigger_setting = self.interface.read_register(self.trigger_block_base_addr)
        assert trigger_setting == 3, "Trigger did not save the value written to it."

        # Configure the trigger_pos, but we'll skip that for now
        print(" -> Setting trigger location...")

        # Start the capture by pulsing request_start
        print(" -> Starting capture...")
        self.interface.write_register(self.request_start_reg_addr, 1)
        self.interface.write_register(self.request_start_reg_addr, 0)

        # Wait for core to finish capturing data
        print(" -> Waiting for capture to complete...")
        state = self.interface.read_register(self.state_reg_addr)
        while(state != self.CAPTURED):
            state = self.interface.read_register(self.state_reg_addr)

        # Read out contents from memory
        print(" -> Reading sample memory contents...")
        addrs = list(range(self.block_memory_base_addr, self.max_addr))
        block_mem_contents = self.interface.read_registers(addrs)

        # Revolve BRAM contents around so the data pointed to by the read_pointer
        # is at the beginning
        print(" -> Reading read_pointer and revolving memory...")
        read_pointer = self.interface.read_register(self.read_pointer_reg_addr)
        return block_mem_contents[read_pointer:] + block_mem_contents[:read_pointer]


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

            # add the data to each probe in the vcd file
            for timestamp in range(0, 2*len(capture_data)):

                # run the clock
                writer.change(clock, timestamp, timestamp % 2 == 0)

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
        playback = VerilogManipulator("logic_analyzer_playback_tmpl.v")

        module_name = f"{self.name}_playback"
        playback.sub(module_name, "/* MODULE_NAME */")

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

class BlockMemoryCore:
    def __init__(self, config, name, base_addr, interface):
        self.name = name
        self.base_addr = base_addr
        self.interface = interface

        # Determine if we expose the BRAM's second port to the top of the module
        if "expose_port" in config:
            assert isinstance(config["expose_port"], bool), "Configuring BRAM exposure must be done with a boolean."
            self.expose_port = config["expose_port"]

        else:
            self.expose_port = True

        # Get depth
        assert "depth" in config, "Depth not specified for Block Memory core."
        assert config["depth"] > 0, "Block Memory core must have positive depth."
        assert isinstance(config["depth"], int), "Block Memory core must have integer depth."
        self.depth = config["depth"]

        # Get width
        assert "width" in config, "Width not specified for Block Memory core."
        assert config["width"] > 0, "Block Memory core must have positive width."
        assert isinstance(config["width"], int), "Block Memory core must have integer width."
        self.width = config["width"]

        self.addr_width = math.ceil(math.log2(self.depth))
        self.n_brams = math.ceil(self.width / 16)
        self.max_addr = self.base_addr + (self.depth * self.n_brams)

    def hdl_inst(self):
        inst = VerilogManipulator("block_memory_inst_tmpl.v")
        inst.sub(self.name, "/* INST_NAME */")
        inst.sub(self.depth, "/* DEPTH */")
        inst.sub(self.width, "/* WIDTH */")
        return inst.get_hdl()

    def hdl_def(self):
        block_memory = VerilogManipulator("block_memory.v").get_hdl()
        dual_port_bram = VerilogManipulator("dual_port_bram.v").get_hdl()
        return block_memory + "\n" + dual_port_bram

    def hdl_top_level_ports(self):
        if not self.expose_port:
            return ""

        tlp = []
        tlp.append(f"input wire {self.name}_clk")
        tlp.append(f"input wire [{self.addr_width-1}:0] {self.name}_addr")
        tlp.append(f"input wire [{self.width-1}:0] {self.name}_din")
        tlp.append(f"output reg [{self.width-1}:0] {self.name}_dout")
        tlp.append(f"input wire {self.name}_we")
        return tlp

    def read(self, addr):
        return self.interface.read_register(addr + self.base_addr)

    def write(self, addr, data):
        return self.interface.write_register(addr + self.base_addr, data)



class Manta:
    def __init__(self, config_filepath):
        config = self.read_config_file(config_filepath)

        # set interface
        if "uart" in config:
            self.interface = UARTInterface(config["uart"])
        else:
            raise ValueError("Unrecognized interface specified.")

        # check that cores were provided
        assert "cores" in config, "No cores found."
        assert len(config["cores"]) > 0, "Must specify at least one core."

        # add cores to self
        base_addr = 0
        self.cores = []
        for i, core_name in enumerate(config["cores"]):
            core = config["cores"][core_name]

            # make sure a type was specified for this core
            assert "type" in core, f"No type specified for core {core_name}."

            # add the core to ourself
            if core["type"] == "logic_analyzer":
                new_core = LogicAnalyzerCore(core, core_name, base_addr, self.interface)

            elif core["type"] == "io":
                new_core = IOCore(core, core_name, base_addr, self.interface)

            elif core["type"] == "lut_ram":
                new_core = LUTRAMCore(core, core_name, base_addr, self.interface)

            elif core["type"] == "block_memory":
                new_core = BlockMemoryCore(core, core_name, base_addr, self.interface)

            else:
                raise ValueError(f"Unrecognized core type specified for {core_name}.")

            # make the next core's base address start one address after the previous one's
            base_addr = new_core.max_addr + 1

            # add friendly name, so users can do Manta.my_logic_analyzer.read() for example
            setattr(self, core_name, new_core)
            self.cores.append(new_core)

    def read_config_file(self, path):
        """Take path to configuration file, and retun the configuration as a python list/dict object."""
        extension = path.split(".")[-1]

        if "json" in extension:
            with open(path, "r") as f:
                import json

                config = json.load(f)

        elif "yaml" in extension or "yml" in extension:
            with open(path, "r") as f:
                import yaml

                config = yaml.safe_load(f)

        else:
            raise ValueError("Unable to recognize configuration file extension.")

        return config

    def gen_connections(self):
        # generates hdl for registers that connect two modules together

        # make pairwise cores
        core_pairs = [(self.cores[i - 1], self.cores[i]) for i in range(1, len(self.cores))]

        conns = []
        for core_pair in core_pairs:
            src = core_pair[0].name
            dst = core_pair[1].name

            hdl = f"reg [15:0] {src}_{dst}_addr;\n"
            hdl += f"reg [15:0] {src}_{dst}_wdata;\n"
            hdl += f"reg [15:0] {src}_{dst}_rdata;\n"
            hdl += f"reg {src}_{dst}_rw;\n"
            hdl += f"reg {src}_{dst}_valid;\n"
            conns.append(hdl)

        return conns

    def gen_instances(self):
        # generates hdl for modules that need to be connected together

        insts = []
        for i, core in enumerate(self.cores):
            # should probably check if core is LogicAnalyzerCore or IOCore

            hdl = core.hdl_inst()

            # connect input
            if (i == 0):
                src_name = "brx"

            else:
                src_name = self.cores[i-1].name
                hdl = hdl.replace(".rdata_i()", f".rdata_i({src_name}_{core.name}_rdata)")

            hdl = hdl.replace(".addr_i()", f".addr_i({src_name}_{core.name}_addr)")
            hdl = hdl.replace(".wdata_i()", f".wdata_i({src_name}_{core.name}_wdata)")
            hdl = hdl.replace(".rw_i()", f".rw_i({src_name}_{core.name}_rw)")
            hdl = hdl.replace(".valid_i()", f".valid_i({src_name}_{core.name}_valid)")



            # connect output
            if (i < len(self.cores)-1):
                dst_name = self.cores[i+1].name
                hdl = hdl.replace(".addr_o()", f".addr_o({core.name}_{dst_name}_addr)")
                hdl = hdl.replace(".wdata_o()", f".wdata_o({core.name}_{dst_name}_wdata)")

            else:
                dst_name = "btx"

            hdl = hdl.replace(".rdata_o()", f".rdata_o({core.name}_{dst_name}_rdata)")
            hdl = hdl.replace(".rw_o()", f".rw_o({core.name}_{dst_name}_rw)")
            hdl = hdl.replace(".valid_o()", f".valid_o({core.name}_{dst_name}_valid)")

            insts.append(hdl)

        return insts

    def gen_core_chain(self):
        insts = self.gen_instances()
        conns = self.gen_connections()
        core_chain = []
        for i, inst in enumerate(insts):
            core_chain.append(inst)

            if (i != len(insts)-1):
                core_chain.append(conns[i])

        return '\n'.join(core_chain)

    def gen_example_inst_ports(self):
        # this is a C-style block comment that contains an instantiation
        # of the configured manta instance - the idea is that a user
        # can copy-paste that into their design instead of trying to spot
        # the difference between their code and the autogenerated code.

        # hopefully this saves time!


        # this turns a list like ['input wire foo', 'output reg bar'] into
        # a nice string like ".foo(foo),\n .bar(bar)"
        interface_ports = self.interface.hdl_top_level_ports()
        interface_ports = [port.split(',')[0] for port in interface_ports]
        interface_ports = [port.split(' ')[-1] for port in interface_ports]
        interface_ports = [f".{port}({port}),\n" for port in interface_ports]
        interface_ports = "".join(interface_ports)

        core_chain_ports = []
        for core in self.cores:
            ports = [port.split(',')[0] for port in core.hdl_top_level_ports()]
            ports = [port.split(' ')[-1] for port in ports]
            ports = [f".{port}({port}), \n" for port in ports]
            ports = "".join(ports)
            ports = "\n" + ports
            core_chain_ports.append(ports)

        core_chain_ports = "\n".join(core_chain_ports)

        ports = interface_ports + core_chain_ports

        # remove trailing comma
        ports = ports.rstrip()
        if ports[-1] == ",":
            ports = ports[:-1]

        return ports

    def gen_top_level_ports(self):
        # get all the top level connections for each module.

        interface_ports = self.interface.hdl_top_level_ports()
        interface_ports = [f"{port},\n" for port in interface_ports]
        interface_ports = "".join(interface_ports) + "\n"

        core_chain_ports = []
        for core in self.cores:
            ports = [f"{port},\n" for port in core.hdl_top_level_ports()]
            ports = "".join(ports)
            core_chain_ports.append(ports)

        core_chain_ports = "\n".join(core_chain_ports)

        ports = interface_ports + core_chain_ports

        # remove trailing comma
        ports = ports.rstrip()
        if ports[-1] == ",":
            ports = ports[:-1]

        return ports

    def gen_interface_rx(self):
        # instantiate interface_rx, substitute in register names
        interface_rx_inst = self.interface.rx_hdl_inst()

        interface_rx_inst = interface_rx_inst.replace("addr_o()", f"addr_o(brx_{self.cores[0].name}_addr)")
        interface_rx_inst = interface_rx_inst.replace("wdata_o()", f"wdata_o(brx_{self.cores[0].name}_wdata)")
        interface_rx_inst = interface_rx_inst.replace("rw_o()", f"rw_o(brx_{self.cores[0].name}_rw)")
        interface_rx_inst = interface_rx_inst.replace("valid_o()", f"valid_o(brx_{self.cores[0].name}_valid)")

        # connect interface_rx to core_chain
        interface_rx_conn= f"""
reg [15:0] brx_{self.cores[0].name}_addr;
reg [15:0] brx_{self.cores[0].name}_wdata;
reg brx_{self.cores[0].name}_rw;
reg brx_{self.cores[0].name}_valid;\n"""

        return interface_rx_inst + interface_rx_conn

    def gen_interface_tx(self):

        # connect core_chain to interface_tx
        interface_tx_conn = f"""
reg [15:0] {self.cores[-1].name}_btx_rdata;
reg {self.cores[-1].name}_btx_rw;
reg {self.cores[-1].name}_btx_valid;\n"""

        # instantiate interface_tx, substitute in register names
        interface_tx_inst = self.interface.tx_hdl_inst()

        interface_tx_inst = interface_tx_inst.replace("addr_i()", f"addr_i({self.cores[0].name}_btx_addr)")
        interface_tx_inst = interface_tx_inst.replace("rdata_i()", f"rdata_i({self.cores[0].name}_btx_rdata)")
        interface_tx_inst = interface_tx_inst.replace("rw_i()", f"rw_i({self.cores[0].name}_btx_rw)")
        interface_tx_inst = interface_tx_inst.replace("valid_i()", f"valid_i({self.cores[0].name}_btx_valid)")

        return interface_tx_conn + interface_tx_inst

    def gen_module_defs(self):
        # aggregate module definitions and remove duplicates
        module_defs_with_dups = [self.interface.rx_hdl_def()] + [core.hdl_def() for core in self.cores] + [self.interface.tx_hdl_def()]
        module_defs = []
        module_defs = [m_def for m_def in module_defs_with_dups if m_def not in module_defs]
        module_defs = [m_def.strip() for m_def in module_defs]
        return '\n\n'.join(module_defs)

    def generate_hdl(self, output_filepath):
        manta = VerilogManipulator("manta_def_tmpl.v")

        manta.sub(version, "/* VERSION */")

        timestamp = datetime.now().strftime("%d %b %Y at %H:%M:%S")
        manta.sub(timestamp, "/* TIMESTAMP */")

        user = os.environ.get("USER", os.environ.get("USERNAME"))
        manta.sub(user, "/* USER */")

        ex_inst_ports = self.gen_example_inst_ports()
        manta.sub(ex_inst_ports, "/* EX_INST_PORTS */")

        top_level_ports = self.gen_top_level_ports()
        manta.sub(top_level_ports, "/* TOP_LEVEL_PORTS */")

        interface_rx = self.gen_interface_rx()
        manta.sub(interface_rx, "/* INTERFACE_RX */")

        core_chain = self.gen_core_chain()
        manta.sub(core_chain, "/* CORE_CHAIN */")

        interface_tx = self.gen_interface_tx()
        manta.sub(interface_tx, "/* INTERFACE_TX */")

        module_defs = self.gen_module_defs()
        manta.sub(module_defs, "/* MODULE_DEFS */")
        return manta.get_hdl()

def main():
    # print help menu if no args passed or help menu requested
    if len(argv) == 1 or argv[1] == "help" or argv[1] == "ray" or argv[1] == "bae":
        print(
            f"""
\033[96m               (\.-./)
\033[96m               /     \\
\033[96m             .'   :   '.
\033[96m        _.-'`     '     `'-._       \033[34;49;1m | \033[34;49;1m Manta v{version} \033[00m
\033[96m     .-'          :          '-.    \033[34;49;1m | \033[34;49;3m An In-Situ Debugging Tool for Programmable Hardware \033[00m
\033[96m   ,'_.._         .         _.._',  \033[34;49;1m | \033[34;49m https://github.com/fischermoseley/manta \033[00m
\033[96m   '`    `'-.     '     .-'`
\033[96m             '.   :   .'            \033[34;49;1m | \033[34;49;3m fischerm [at] mit.edu \033[00m
\033[96m               \_. ._/
\033[96m         \       |^|
\033[96m          |      | ;
\033[96m          \\'.___.' /
\033[96m           '-....-'  \033[00m

Supported commands:
    gen [config file] [path]                            generate a verilog module with the given configuration, and save to the provided path
    capture  [config file] [LA core] [path] [path]      start a capture on the specified core, and save the results to a .mem or .vcd file at the provided path
    playback [config file] [LA core] [path]             generate a verilog module that plays back a capture from a given logic analyzer core, and save to the provided path
    ports                                               list all available serial ports
    help, ray                                           display this splash screen (hehe...splash screen)
"""
        )

    # list available serial ports
    elif argv[1] == "ports":
        import serial.tools.list_ports

        for port in serial.tools.list_ports.comports():
            print(port)
            print(' ->  vid: 0x{:04X}'.format(port.vid))
            print(' ->  pid: 0x{:04X}'.format(port.pid))
            print(f" ->  ser: {port.serial_number}")
            print(f" ->  loc: {port.location}")
            print(f" -> mftr: {port.manufacturer}")
            print(f" -> prod: {port.product}")
            print(f" -> desc: {port.description}\n")

    # generate the specified configuration
    elif argv[1] == "gen":
        assert len(argv) == 4, "Wrong number of arguments, run 'manta help' for proper usage."

        m = Manta(argv[2])
        hdl = m.generate_hdl(argv[3])
        with open(argv[3], "w") as f:
            f.write(hdl)

    # run the specified core
    elif argv[1] == "capture":
        assert len(argv) >= 5, "Wrong number of arguments, run 'manta help' for proper usage."

        m = Manta(argv[2])
        la = getattr(m, argv[3])
        data = la.capture()

        for path in argv[4:]:
            if ".vcd" in path:
                la.export_vcd(data, path)

            elif ".mem" in path:
                la.export_mem(data, path)

            else:
                print(f"Warning: Unknown output file format for {path}, skipping...")

    elif argv[1] == "playback":
        assert len(argv) == 5, "Wrong number of arguments, run 'manta help' for proper usage."

        m = Manta(argv[2])
        la = getattr(m, argv[3])
        la.export_playback_module(argv[4])

    else:
        print("Option not recognized, run 'manta help' for proper usage.")


if __name__ == "__main__":
    main()
