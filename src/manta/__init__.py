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

    def tx_hdl(self):
        pkgutil.get_data(__name__, "uart_tx.sv").decode()

    def rx_hdl(self):
        pkgutil.get_data(__name__, "rx_uart.sv").decode()

class IOCore:
    def __init__(self, config, interface):
        self.interface = interface
        
class LogicAnalyzerCore:
    def __init__(self, config, interface):
        self.interface = interface

        # load config
        assert "sample_depth" in config, "Sample depth not found for logic analyzer core."
        self.sample_depth = config["sample_depth"]

        assert "probes" in config, "No probe definitions found."
        assert len(config["probes"]) > 0, "Must specify at least one probe."

        for probe_name, probe_width in config["probes"].items():
            assert probe_width > 0, f"Probe {probe_name} is of invalid width - it must be of at least width one."

        self.probes = config["probes"]

        assert "triggers" in config, "No triggers found."
        assert len(config["triggers"]) > 0, "Must specify at least one trigger."
        self.triggers = config["triggers"]

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

    def hdl(self):
        # Return an autogenerated verilog module definition for the core.
        # load source files
        tmpl = pkgutil.get_data(__name__, "la_template.v").decode()

        # add triggers
        trigger = [f"({trigger})" for trigger in self.triggers]
        trigger = " || ".join(trigger)
        templ = templ.replace("@TRIGGER", trigger)

        # add concat
        concat = [name for name in self.probes]
        concat = ", ".join(concat)
        concat = "{" + concat + "}"
        templ = templ.replace("@CONCAT", concat)

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
            
            else:
                raise ValueError(f"Unrecognized core type specified for {core_name}.")

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

    def generate(self):
        # this occurs in two steps: generating manta and the top-level,
        # and pasting in all the HDL from earlier.

        uart_rx_hdl = pkgutil.get_data(__name__, "rx_uart.sv").decode()
        bridge_rx_hdl = pkgutil.get_data(__name__, "bridge_rx.sv").decode()
        bridge_tx_hdl = pkgutil.get_data(__name__, "bridge_tx.sv").decode()
        uart_tx_hdl = pkgutil.get_data(__name__, "uart_tx.sv").decode()

        # make pairwise cores
        core_pairs = [(cores[i-1], cores[i]) for i in range(1, len(cores))]

        # write HDL to instantiate and connect them
        connections = [] 
        for src, dest in core_pairs:
            # wait who's source and who's destination? have to know both the src, dest,
            # and also current core at any given moment

            # so then is the solution src src_current current current_dst dst
            hdl =  src.inst()
            hdl += hdl.replace(".addr_i()",  f".addr_i({src}_{dest}_addr)")
            hdl += hdl.replace(".wdata_i()", f".wdata_i({src}_{dest}_wdata)")
            hdl += hdl.replace(".rdata_i()", f".rdata_i({src}_{dest}_rdata)")
            hdl += hdl.replace(".rw_i()",    f".rw_i({src}_{dest}_rw)")
            hdl += hdl.replace(".valid_i()", f".valid_i({src}_{dest}_valid)")

            hdl += "\n"
            hdl += f"reg[15:0] {src}_{dest}_addr\n"
            hdl += f"reg[15:0] {src}_{dest}_wdata\n"
            hdl += f"reg[15:0] {src}_{dest}_rdata\n"
            hdl += f"reg {src}_{dest}_rw\n"
            hdl += f"reg {src}_{dest}_valid\n\n"
            connections.append(hdl)
    
        # write HDL to instantiate them, now that we know src and dest
        instantiations = [] 
        for core in cores:
            hdl = core.inst() 
            hdl = hdl.replace(".addr_i()", f".addr_i({src}_{dest}_addr)")
            hdl = hdl.replace(".addr_i()", f".addr_i({src}_{dest}_addr)")
        
        # for core in cores:
        #     registers = ''
        #     registers += f'{core}{}'
        # # wire cores together

        # add preamble to top of file
        user = os.environ.get("USER", os.environ.get("USERNAME"))
        timestamp = datetime.now().strftime("%d %b %Y at %H:%M:%S")

        hdl = "This manata definitinon was autogenerated on {timestamp} by {user}\n\n"
        hdl += "If this breaks or if you've got dank formal verification memes,\n"
        hdl += "please contact fischerm [at] mit.edu\n"


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
        with open(argv[3], "w") as f:
            f.write(manta.generate())

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
