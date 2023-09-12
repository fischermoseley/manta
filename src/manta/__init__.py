# Internal Dependencies
from .utils import *
from .la_core import *
from .io_core import *
from .block_mem_core import *

# External Dependencies
from sys import argv
import os
from datetime import datetime
from pkg_resources import get_distribution

class Manta:
    def __init__(self, config_filepath):
        config = self.read_config_file(config_filepath)

        # set interface
        if "uart" in config:
            from .uart_iface import UARTInterface
            self.interface = UARTInterface(config["uart"])

        elif "ethernet" in config:
            from .ether_iface import EthernetInterface
            self.interface = EthernetInterface(config["ethernet"])

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

            elif core["type"] == "block_memory":
                new_core = BlockMemoryCore(core, core_name, base_addr, self.interface)

            else:
                raise ValueError(f"Unrecognized core type specified for {core_name}.")

            # make sure we're not out of address space
            assert new_core.max_addr < (2**16)-1, f"Ran out of address space to allocate to core {core_name}."

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
            hdl += f"reg [15:0] {src}_{dst}_data;\n"
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

            hdl = hdl.replace(".addr_i()", f".addr_i({src_name}_{core.name}_addr)")
            hdl = hdl.replace(".data_i()", f".data_i({src_name}_{core.name}_data)")
            hdl = hdl.replace(".rw_i()", f".rw_i({src_name}_{core.name}_rw)")
            hdl = hdl.replace(".valid_i()", f".valid_i({src_name}_{core.name}_valid)")



            # connect output
            if (i < len(self.cores)-1):
                dst_name = self.cores[i+1].name
                hdl = hdl.replace(".addr_o()", f".addr_o({core.name}_{dst_name}_addr)")

            else:
                dst_name = "btx"

            hdl = hdl.replace(".data_o()", f".data_o({core.name}_{dst_name}_data)")
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
        interface_rx_inst = interface_rx_inst.replace("data_o()", f"data_o(brx_{self.cores[0].name}_data)")
        interface_rx_inst = interface_rx_inst.replace("rw_o()", f"rw_o(brx_{self.cores[0].name}_rw)")
        interface_rx_inst = interface_rx_inst.replace("valid_o()", f"valid_o(brx_{self.cores[0].name}_valid)")

        # connect interface_rx to core_chain
        interface_rx_conn= f"""
reg [15:0] brx_{self.cores[0].name}_addr;
reg [15:0] brx_{self.cores[0].name}_data;
reg brx_{self.cores[0].name}_rw;
reg brx_{self.cores[0].name}_valid;\n"""

        return interface_rx_inst + interface_rx_conn

    def gen_interface_tx(self):

        # connect core_chain to interface_tx
        interface_tx_conn = f"""
reg [15:0] {self.cores[-1].name}_btx_data;
reg {self.cores[-1].name}_btx_rw;
reg {self.cores[-1].name}_btx_valid;\n"""

        # instantiate interface_tx, substitute in register names
        interface_tx_inst = self.interface.tx_hdl_inst()

        interface_tx_inst = interface_tx_inst.replace("addr_i()", f"addr_i({self.cores[-1].name}_btx_addr)")
        interface_tx_inst = interface_tx_inst.replace("data_i()", f"data_i({self.cores[-1].name}_btx_data)")
        interface_tx_inst = interface_tx_inst.replace("rw_i()", f"rw_i({self.cores[-1].name}_btx_rw)")
        interface_tx_inst = interface_tx_inst.replace("valid_i()", f"valid_i({self.cores[-1].name}_btx_valid)")

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

        version = "v" + get_distribution('mantaray').version
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

        manta.hdl = "`timescale 1ns/1ps\n" + manta.hdl
        manta.hdl = "`default_nettype none\n"+ manta.hdl
        manta.hdl = manta.hdl + "\n`default_nettype wire"

        return manta.get_hdl()

def main():
    # print help menu if no args passed or help menu requested

    if len(argv) == 1 or argv[1] == "help" or argv[1] == "ray" or argv[1] == "bae":
        version = "v" + get_distribution('mantaray').version
        print(
            f"""
\033[96m               (\.-./)
\033[96m               /     \\
\033[96m             .'   :   '.
\033[96m        _.-'`     '     `'-._       \033[34;49;1m | \033[34;49;1m Manta {version} \033[00m
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
    gen [config_file] [verilog_file]                                generate a verilog file specifying the Manta module from a given configuration file, and save to the provided path
    capture  [config_file] [LA_core_name] [vcd_file] [mem_file]     start a capture on the specified core, and save the results to a .mem or .vcd file at the provided path(s)
    playback [config file] [LA_core_name] [verilog_file]            generate a verilog module that plays back a capture from a given logic analyzer core, and save to the provided path
    ports                                                           list all available serial ports
    help, ray                                                       display this splash screen (hehe...splash screen)
"""
        )

    # list available serial ports
    elif argv[1] == "ports":
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            print(port)

            # sometimes macOS will enumerate non-serial devices as serial ports,
            # in which case the PID/VID/serial/location/etc are all None
            pid = f"0x{port.vid:04X}" if port.pid is not None else "None"
            vid = f"0x{port.vid:04X}" if port.vid is not None else "None"

            print(f" ->  pid: {pid}")
            print(f" ->  vid: {vid}")
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
