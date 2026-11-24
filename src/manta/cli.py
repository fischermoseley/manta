import argparse
from importlib.metadata import version

from manta.manta import Manta
from manta.utils import *

logo = f"""
                                        .
                                      .';
                                     (  (
                                 .    `. `.
                                  `.. .'   )
                                   ; `;   .'.--.
                                  :'      `.' ('
                                .;'            :
                         ______:..._____     ./'
                      .-"                "-.(
(`-.__             .-' ..              ..   `-.             __......')
 `:   `-...     .-'   :* :            :* :     `-.     ...-'       :'
   `-.     `\"""'      `--'            `--'        `""\"'         .-'
      `-.         .     .-.           .--.     `.            .-'
         `-.     : .'. (   `--_____--'    )  `. ;         .-'
            `--..`.`.`  `--...       ..--' .'.'.'    ..--'
                 `---...      ````'''         ...---'
                        `------........------'


Manta - A configurable and approachable tool for FPGA debugging and rapid prototyping
Version {version("manta-fpga")}
https://github.com/fischermoseley/manta
"""


def gen(config_path, output_path):
    manta = Manta.from_config(config_path)
    manta.generate_verilog(output_path)


def inst(config_path):
    manta = Manta.from_config(config_path)
    ports = manta.get_top_level_ports()
    hdl = ",\n    ".join([f".{p.name}({p.name})" for p in ports])

    header = """
manta manta_inst(
    .clk(clk),
    .rst(rst),
    """

    return header + hdl + ");\n"


def capture(config_path, logic_analyzer_name, export_paths):
    manta = Manta.from_config(config_path)
    la = getattr(manta.cores, logic_analyzer_name)
    cap = la.capture()

    for path in export_paths:
        if ".vcd" in path:
            cap.export_vcd(path)
        elif ".csv" in path:
            cap.export_csv(path)
        elif ".v" in path:
            cap.export_playback_verilog(path)
        else:
            warn(f"Unrecognized file type, skipping {path}.")


def ports():
    import serial.tools.list_ports

    for port in serial.tools.list_ports.comports():
        print(port)

        # Sometimes macOS will enumerate non-serial devices as serial ports,
        # in which case the PID/VID/serial/location/etc are all None
        pid = f"0x{port.pid:04X}" if port.pid is not None else "None"
        vid = f"0x{port.vid:04X}" if port.vid is not None else "None"

        print(f" ->  pid: {pid}")
        print(f" ->  vid: {vid}")
        print(f" ->  ser: {port.serial_number}")
        print(f" ->  loc: {port.location}")
        print(f" -> mftr: {port.manufacturer}")
        print(f" -> prod: {port.product}")
        print(f" -> desc: {port.description}\n")


class PrintVersion(argparse.Action):  # needed so ASCII art prints correctly
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print(logo)
        parser.exit()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="manta",
        description="Manta - A configurable and approachable tool for FPGA debugging and rapid prototyping",
    )
    parser.add_argument(
        "--version",
        action=PrintVersion,
        help="show version info and exit",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # gen
    p = subparsers.add_parser("gen", help="generate Verilog for the Manta module")
    p.add_argument("config", help="path to the Manta config file")
    p.add_argument("output", help="path to write the generated Verilog to")

    # inst
    p = subparsers.add_parser(
        "inst",
        help="print a Verilog snippet to instantiate Manta",
    )
    p.add_argument("config", help="path to the Manta config file")

    # capture
    p = subparsers.add_parser(
        "capture",
        help="capture data from a logic analyzer core",
    )
    p.add_argument("config", help="path to the Manta config file")
    p.add_argument("core", help="name of the logic analyzer core")
    p.add_argument(
        "outputs",
        nargs="+",
        help="output path(s), .vcd, .csv, or .v",
    )

    # ports
    subparsers.add_parser("ports", help="list available serial ports")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()

    elif args.command == "gen":
        gen(args.config, args.output)

    elif args.command == "inst":
        print(inst(args.config))

    elif args.command == "capture":
        capture(args.config, args.core, args.outputs)

    elif args.command == "ports":
        ports()


if __name__ == "__main__":
    main()
