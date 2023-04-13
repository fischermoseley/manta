import pkgutil
from sys import argv
import os
from datetime import datetime

version = "0.0.0"

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

        # confirm core clock is sufficiently fast
        clocks_per_baud = self.clock_freq // self.baudrate
        assert clocks_per_baud >= 2
        self.clocks_per_baud = clocks_per_baud

        # confirm we can match baudrate suffeciently well
        actual_baudrate = self.clock_freq / clocks_per_baud
        baudrate_error = 100 * abs(actual_baudrate - self.baudrate) / self.baudrate
        assert (
            baudrate_error <= 5
        ), "Unable to match target baudrate - they differ by {baudrate_error}%"

        # set verbosity
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

    def read_register(self, addr):
        self.open_port_if_not_alredy_open()

        # request from the bus
        addr_str = '{:04X}'.format(addr)
        request = f"M{addr_str}\r\n".encode('ascii')

        self.ser.write(request)

        # read and parse the response
        response = self.ser.read(7)

        assert response is not None, "No reponse received."
        response = response.decode('ascii')
        assert response[0] == 'M', "Bad message recieved, incorrect preamble."
        assert response[-1] == '\n', "Bad message received, incorrect EOL."
        assert response[-2] == '\r', "Bad message received, incorrect EOL."
        assert len(response) == 7, f"Wrong number of bytes received, expecting 7 but got {len(response)}."

        data = int(response[1:5], 16)
        data_hex ='{:04X}'.format(data)


        if self.verbose:
            print(f"read {data_hex} from {addr_str}")

        return data

    def write_register(self, addr, data):
        self.open_port_if_not_alredy_open()

        # request from the bus
        addr_str = '{:04X}'.format(addr)
        data_str = '{:04X}'.format(data)
        request = f"M{addr_str}{data_str}\r\n"

        if self.verbose:
            print(f"wrote {data_str} to {addr_str}")

        self.ser.write(request.encode('ascii'))

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


        # compute addresses
        # - need 3 addresses for configuration (state, current_loc, trigger_loc)
        #   and 2 address for each trigger (operation and argument)

        self.fsm_base_addr = self.base_addr
        self.trigger_block_base_addr = self.fsm_base_addr + 3
        self.sample_mem_base_addr = self.trigger_block_base_addr + (2*len(self.probes))
        self.max_addr = self.sample_mem_base_addr + self.sample_depth

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

    def gen_sample_mem_def(self):
        sample_mem = VerilogManipulator("sample_mem_def_tmpl.v")

        # add probe ports to module declaration
        # - these are the ports that belong to the logic analyzer, but
        #   need to be included in the trigger_block module declaration
        probe_ports = sample_mem.net_dec(self.probes, "input wire", trailing_comma=True)
        sample_mem.sub(probe_ports, "/* PROBE_PORTS */")

        # concatenate probes to BRAM input
        total_probe_width = sum([width for name, width in self.probes.items()])

        if total_probe_width > 16:
            # TODO: implement > 16 bit addressing
            raise NotImplementedError("ummm i'm getting around to it calm down calm down")

        zero_pad_width = 16 - total_probe_width
        concat = ", ".join([name for name in self.probes])
        concat = f"{{{zero_pad_width}'b0, {concat}}}"

        sample_mem.sub(concat, "/* CONCAT */")
        return sample_mem.get_hdl()

    def gen_logic_analyzer_def(self):
        la = VerilogManipulator("logic_analyzer_def_tmpl.v")

        # add top level probe ports to module declaration
        ports = la.net_dec(self.probes, "input wire", trailing_comma=True)
        la.sub(ports, "/* TOP_LEVEL_PROBE_PORTS */")

        # assign base addresses to the FSM, trigger block, and sample mem
        la.sub(self.fsm_base_addr, "/* FSM_BASE_ADDR */")
        la.sub(self.trigger_block_base_addr, "/* TRIGGER_BLOCK_BASE_ADDR */")
        la.sub(self.sample_mem_base_addr, "/* SAMPLE_MEM_BASE_ADDR */")

        # set sample depth
        la.sub(self.sample_depth, "/* SAMPLE_DEPTH */")

        # set probe ports for the trigger block and sample mem
        probe_ports = la.net_conn(self.probes, trailing_comma=True)
        la.sub(probe_ports, "/* TRIGGER_BLOCK_PROBE_PORTS */")
        la.sub(probe_ports, "/* SAMPLE_MEM_PROBE_PORTS */")

        return la.get_hdl()

    def hdl_def(self):
        # Return an autogenerated verilog module definition for the core.
        # load source files
        la_fsm = VerilogManipulator("la_fsm.v").get_hdl()
        dual_port_bram = VerilogManipulator("dual_port_bram.v").get_hdl()
        trigger = VerilogManipulator("trigger.v").get_hdl()
        trigger_block = self.gen_trigger_block_def()
        sample_mem = self.gen_sample_mem_def()
        logic_analyzer = self.gen_logic_analyzer_def()

        return logic_analyzer + la_fsm + sample_mem + dual_port_bram + trigger_block + trigger

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

    def run(self):
        pass

    def part_select(self, data, width):
        top, bottom = width

        assert top >= bottom

        mask = 2 ** (top - bottom + 1) - 1
        return (data >> bottom) & mask

    def make_widths(self, config):
        # {probe0, probe1, probe2}
        # [12, 1, 3] should produce
        # [ (15, 4) (3, 3) (2,0) ]

        widths = list(config["downlink"]["probes"].values())

        # easiest to make by summing them and incrementally subtracting
        s = sum(widths)
        slices = []
        for width in widths:
            slices.append((s - 1, s - width))
            s = s - width

        assert s == 0, "Probe sizes are weird, cannot slice bits properly"
        return slices

    def export_waveform(self, config, data, path):
        extension = path.split(".")[-1]

        assert extension == "vcd", "Unrecognized waveform export format."
        from vcd import VCDWriter

        vcd_file = open(path, "w")

        # Use the datetime format that iVerilog uses
        timestamp = datetime.now().strftime("%a %b %w %H:%M:%S %Y")

        with VCDWriter(
            vcd_file, timescale="10 ns", date=timestamp, version="manta"
        ) as writer:
            # add probes to vcd file
            vcd_probes = []
            for name, width in config["downlink"]["probes"].items():
                probe = writer.register_var("manta", name, "wire", size=width)
                vcd_probes.append(probe)

            # add clock to vcd file
            clock = writer.register_var("manta", "clk", "wire", size=1)

            # calculate bit widths for part selecting
            widths = self.make_widths(config)

            # slice data, and dump to vcd file
            for timestamp in range(2 * len(data)):
                value = data[timestamp // 2]

                # dump clock values to vcd file
                # note: this assumes logic is triggered
                # on the rising edge of the clock, @TODO fix this
                writer.change(clock, timestamp, timestamp % 2 == 0)

                for probe_num, probe in enumerate(vcd_probes):
                    val = self.part_select(value, widths[probe_num])
                    writer.change(probe, timestamp, val)
        vcd_file.close()

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

        from math import ceil, floor, log2
        self.addr_width = ceil(log2(self.depth))
        self.n_brams = ceil(self.width / 16)
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
    gen [config file]       generate the core specified in the config file
    run [config file]       run the core specified in the config file
    ports                   list all available serial ports
    help, ray               display this splash screen (hehe...splash screen)
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
        assert (
            len(argv) == 4
        ), "Wrong number of arguments, only a config file and output file must both be specified."

        manta = Manta(argv[2])
        hdl = manta.generate_hdl(argv[3])
        with open(argv[3], "w") as f:
            f.write(hdl)

    # run the specified core
    elif argv[1] == "run":
        assert (
            len(argv) == 4
        ), "Wrong number of arguments, only a config file and output file must both be specified."

        manta = Manta(argv[2])
        manta.la_0.arm()
        manta.la_0.export_waveform(argv[3])

    else:
        print("Option not recognized! Run 'manta help' for supported commands.")


if __name__ == "__main__":
    main()
