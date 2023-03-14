import pkgutil
from sys import argv
import os
from datetime import datetime

version = "0.0.0"


class UARTInterface:
    def __init__(self, config):
        # Obtain port. No way to check if it's valid yet.
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

    def open(self):
        import serial

        self.ser = serial.Serial(self.port, self.baudrate)

    def read(self, bytes):
        self.ser.read(bytes)

    def write(self, bytes):
        self.ser.write(bytes)  

    def hdl_top_level_ports(self):
        # this should return the probes that we want to connect to top-level, but like as a string of verilog

        return ["input wire rx", "output reg tx"]

    def rx_hdl_def(self):
        uart_rx_def = pkgutil.get_data(__name__, "rx_uart.v").decode()
        bridge_rx_def = pkgutil.get_data(__name__, "bridge_rx.v").decode()
        return uart_rx_def + '\n' + bridge_rx_def

    def tx_hdl_def(self):
        uart_tx_def = pkgutil.get_data(__name__, "uart_tx.v").decode()
        bridge_tx_def = pkgutil.get_data(__name__, "bridge_tx.v").decode()
        return bridge_tx_def + '\n' + uart_tx_def

    def rx_hdl_inst(self):
        return f"""
    rx_uart #(.CLOCKS_PER_BAUD({self.clocks_per_baud})) urx (
        .i_clk(clk),
        .i_uart_rx(rx),
        .o_wr(urx_brx_axiv),
        .o_data(urx_brx_axid));

    logic [7:0] urx_brx_axid;
    logic urx_brx_axiv;

    bridge_rx brx (
        .clk(clk),

        .rx_data(urx_brx_axid),
        .rx_valid(urx_brx_axiv),

        .addr_o(),
        .wdata_o(),
        .rw_o(),
        .valid_o());
        """
    
    def tx_hdl_inst(self):
        return f"""
    bridge_tx btx (
        .clk(clk),
        
        .rdata_i(),
        .rw_i(),
        .valid_i(),

        .ready_i(utx_btx_ready),
        .data_o(btx_utx_data),
        .valid_o(btx_utx_valid));

    logic utx_btx_ready;
    logic btx_utx_valid;
    logic [7:0] btx_utx_data;
    
    uart_tx #(.CLOCKS_PER_BAUD({self.clocks_per_baud})) utx (
        .clk(clk),

        .data(btx_utx_data),
        .valid(btx_utx_valid),
        .ready(utx_btx_ready),

        .tx(tx));\n"""


class LUTRAMCore:
    def __init__(self, config, interface):
        self.interface = interface

        assert "size" in config, "Size not specified for LUT RAM core."
        self.size = config["size"]
    
    def hdl_inst(self):
        hdl = f"""
    lut_ram #(.DEPTH({self.size})) {self.name} (
        .clk(clk),

        .addr_i(),
        .wdata_i(),
        .rdata_i(),
        .rw_i(),
        .valid_i(),

        .addr_o(),
        .wdata_o(),
        .rdata_o(),
        .rw_o(),
        .valid_o());\n"""
    
        return hdl

    def hdl_def(self):
        hdl = pkgutil.get_data(__name__, "lut_ram.v").decode()
        return hdl

    def hdl_top_level_ports(self):
        # no top_level connections since this core just lives on the bus
        return []

class LogicAnalyzerCore:
    def __init__(self, config, interface):
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
    
    def hdl_inst(self):
        ports = []

        ports = [f".{name}({name})," for name in self.probes.keys()]
        ports = "\n\t\t".join(ports)
        
        hdl = f"""
    la_core {self.name} (
        .clk(clk),

        .addr_i(),
        .wdata_i(),
        .rdata_i(),
        .rw_i(),
        .valid_i(),

        {ports}
        
        .addr_o(),
        .wdata_o(),
        .rdata_o(),
        .rw_o(),
        .valid_o());\n"""
    
        return hdl

    def run(self):
        self.interface.open()
        self.interface.flushInput()
        self.interface.write(b"\x30")
        data = self.interface.read(4096)

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

    def hdl_def(self):
        # Return an autogenerated verilog module definition for the core.
        # load source files
        tmpl = pkgutil.get_data(__name__, "la_template.v").decode()

        # add triggers
        trigger = [f"({trigger})" for trigger in self.triggers]
        trigger = " || ".join(trigger)
        tmpl = tmpl.replace("@TRIGGER", trigger)

        # add concat
        concat = [name for name in self.probes]
        concat = ", ".join(concat)
        concat = "{" + concat + "}"
        tmpl = tmpl.replace("@CONCAT", concat)

        # add probes
        probe_verilog = []
        for name, width in self.probes.items():
            if width == 1:
                probe_verilog.append(f"input wire {name},")

            else:
                probe_verilog.append(f"input wire [{width-1}:0] {name},")

        probe_verilog = "\n\t\t".join(probe_verilog)
        tmpl = tmpl.replace("@PROBES", probe_verilog)

        # add sample width
        sample_width = sum([width for name, width in self.probes.items()])
        tmpl = tmpl.replace("@SAMPLE_WIDTH", str(sample_width))

        # add sample depth
        tmpl = tmpl.replace("@SAMPLE_DEPTH", str(self.sample_depth))
        return tmpl

    def hdl_top_level_ports(self):
        # this should return the probes that we want to connect to top-level, but as a list of verilog ports
        
        ports = []
        for name, width in self.probes.items():
            if width == 1:
                ports.append(f"input wire {name}")
            else:
                ports.append(f"input wire [{width-1}:0] {name}")
            
        return ports

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
        self.cores = []
        for i, core_name in enumerate(config["cores"]):
            core = config["cores"][core_name]

            # make sure a type was specified for this core
            assert "type" in core, f"No type specified for core {core_name}."

            # add the core to ourself
            if core["type"] == "logic_analyzer":
                new_core = LogicAnalyzerCore(core, self.interface)

            elif core["type"] == "io":
                new_core = IOCore(core, self.interface)
            
            elif core["type"] == "lut_ram":
                new_core = LUTRAMCore(core, self.interface)

            else:
                raise ValueError(f"Unrecognized core type specified for {core_name}.")

            # TODO: update class defs so that we don't monkey-patch like this. this is not good. i am lazy
            setattr(new_core, 'name', core_name)

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

    def generate_connections(self):
        # generates hdl for registers that connect two modules together

        # make pairwise cores
        core_pairs = [(self.cores[i - 1], self.cores[i]) for i in range(1, len(self.cores))]
        
        conns = []
        for core_pair in core_pairs:
            src = core_pair[0].name
            dst = core_pair[1].name

            hdl = f"\treg [15:0] {src}_{dst}_addr;\n"
            hdl += f"\treg [15:0] {src}_{dst}_wdata;\n"
            hdl += f"\treg [15:0] {src}_{dst}_rdata;\n"
            hdl += f"\treg {src}_{dst}_rw;\n"
            hdl += f"\treg {src}_{dst}_valid;\n"
            conns.append(hdl)
        
        return conns

    def generate_instances(self):
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
                dst_name = self.cores[i+1]
                hdl = hdl.replace(".addr_o()", f".addr_o({core.name}_{dst_name}_addr)")
                hdl = hdl.replace(".wdata_o()", f".wdata_o({core.name}_{dst_name}_wdata)")
            
            else:
                dst_name = "btx"

            hdl = hdl.replace(".rdata_o()", f".rdata_o({core.name}_{dst_name}_rdata)")
            hdl = hdl.replace(".rw_o()", f".rw_o({core.name}_{dst_name}_rw)")
            hdl = hdl.replace(".valid_o()", f".valid_o({core.name}_{dst_name}_valid)")

            insts.append(hdl)
        
        return insts

    def generate_core_chain(self):
        insts = self.generate_instances()
        conns = self.generate_connections()
        core_chain = []
        for i, inst in enumerate(insts):
            core_chain.append(inst)

            if (i != len(insts)-1):
                core_chain.append(conns[i])
        
        return '\n'.join(core_chain)

    def generate_header(self):
        # generate header
        user = os.environ.get("USER", os.environ.get("USERNAME"))
        timestamp = datetime.now().strftime("%d %b %Y at %H:%M:%S")

        header = f"""
/*
This manta definition was generated on {timestamp} by {user}

If this breaks or if you've got dank formal verification memes,
please contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.
*/
"""
        return header

    def generate_declaration(self):
        # get all the top level connections for each module.

        interface_ports = self.interface.hdl_top_level_ports()
        interface_ports = [f"    {port},\n" for port in interface_ports]
        interface_ports = "".join(interface_ports) + "\n"

        core_chain_ports = []
        for core in self.cores:
            ports = [f"    {port},\n" for port in core.hdl_top_level_ports()]
            ports = "".join(ports)
            core_chain_ports.append(ports)
        
        core_chain_ports = "\n".join(core_chain_ports)

        ports = interface_ports + core_chain_ports

        # remove trailing comma
        ports = ports.rstrip()
        if ports[-1] == ",":
            ports = ports[:-1]

        print(ports)

        return f"""
module manta (
    input wire clk,

{ports});
"""

    def generate_interface_rx(self):
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

    def generate_interface_tx(self):

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

    def generate_footer(self):
        return """endmodule\n""" 
    
    def generate_module_defs(self):
        # aggregate module definitions and remove duplicates
        module_defs_with_dups = [self.interface.rx_hdl_def()] + [core.hdl_def() for core in self.cores] + [self.interface.tx_hdl_def()]
        module_defs = []
        module_defs = [m_def for m_def in module_defs_with_dups if m_def not in module_defs]
        return '\n'.join(module_defs)



    def generate_hdl(self, output_filepath):
        """
        This function generates manta.v, which has the following anatomy:
        - Header - contains a little blurb about when and who generated the file 
        - Top-Level Module - the actual definition of module manta
            - Declaration - contains `module manta` and top-level ports 
                            that constitutent cores need access to
            - Interface RX - the modules needed to bring whatever interface the user
                             selected onto the bus. For UART, this is just an instance
                             of uart_rx and bridge_rx.
            - Core Chain - the chain of cores specified by the user. This follows
                           a sequence of:
                - Core Instance - HDL specifying an instance of the core. 
                - Core Connection - HDL specifying the registers that connect one
                                    core to the next.
                - Core Instance 
                - Core Connection
                ....
                
                This repeats for however many cores the user specified.

            - Interface TX - the modules needed to bring the bus out to whatever
                             interface the user selected. For UART, this is just
                             an instance of bridge_tx and uart_tx.
            - Footer - just the 'endmodule' keyword.

        - Module Definitions - all the source for the modules instantiated in the
                               top-level module. 
        """

        # generate header
        header = self.generate_header()

        # generate module declaration
        declar = self.generate_declaration()

        # generate interface_rx
        interface_rx = self.generate_interface_rx() 
        
        # generate core chain 
        core_chain = self.generate_core_chain()
        
        # generate interface_tx
        interface_tx = self.generate_interface_tx()

        # generate footer
        footer = self.generate_footer()

        # generate module definitions
        module_defs = self.generate_module_defs()
        
        # assemble all the parts
        hdl = header + declar + interface_rx + core_chain + interface_tx + footer
        hdl += "\n /* ---- Module Definitions ----  */\n"
        hdl += module_defs

        # default_nettype and timescale directives only at the beginning and end
        hdl = hdl.replace("`default_nettype none", "")
        hdl = hdl.replace("`default_nettype wire", "")
        hdl = hdl.replace("`timescale 1ns/1ps", "")

        hdl = "`default_nettype none\n" + "`timescale 1ns/1ps\n" + hdl + "`default_nettype wire"

        with open(output_filepath, 'w') as f:
            f.write(hdl)        


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
    terminal [config file]  present a minicom-like serial terminal with the UART settings in the config file
    ports                   list all available serial ports
    help, ray               display this splash screen (hehe...splash screen)
"""
        )

    # open minicom-like serial terminal with given config
    elif argv[1] == "terminal":
        assert len(argv) == 3, "Not enough (or too many) config files specified."

        # TODO: make this work with a looser config file - it should work as long as it has a uart definition
        manta = Manta(argv[2])

        raise NotImplementedError("Miniterm console is still under development!")

    # list available serial ports
    elif argv[1] == "ports":
        import serial.tools.list_ports

        for info in serial.tools.list_ports.comports():
            print(info)

    # generate the specified configuration
    elif argv[1] == "gen":
        assert (
            len(argv) == 4
        ), "Wrong number of arguments, only a config file and output file must both be specified."

        manta = Manta(argv[2])
        manta.generate(argv[3])

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
