from importlib.metadata import distribution
from sys import argv

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
Version {distribution("manta-fpga").version}
https://github.com/fischermoseley/manta
"""


usage = """
Usage:
    gen [config_file] [verilog_file]
            Generate a verilog file specifying the Manta module from a given
            configuration file, and save to the provided path.

    inst [config_file]
            Generate a copy-pasteable Verilog snippet to instantiate Manta
            in your design.

    capture [config_file] [la_core_name] [output path] [[additional output paths]...]
            Start a capture on the specified core, and save the results to a .vcd,
            .csv, or .v file at the provided path(s).

    ports
            List all available serial ports.

    help
            Display this help menu.

    version
            Display the currently installed version."""


def help():
    print(usage)


def version():
    print(logo)


def wrong_args():
    print('Wrong number of arguments, run "manta help" for usage.')
    exit(1)


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


def main():
    if len(argv) == 1:
        help()

    elif argv[1] in ["help", "-h", "-help", "--help", "ray"]:
        help()

    elif argv[1] == "gen":
        if len(argv) != 4:
            wrong_args()
        gen(argv[2], argv[3])

    elif argv[1] == "inst":
        if len(argv) != 3:
            wrong_args()

        print(inst(argv[2]))

    elif argv[1] == "capture":
        if len(argv) < 5:
            wrong_args()
        capture(argv[2], argv[3], argv[4:])

    elif argv[1] == "ports":
        ports()

    elif argv[1] == "version":
        version()

    else:
        wrong_args()


if __name__ == "__main__":
    main()
