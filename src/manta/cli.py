from .manta import Manta
from warnings import warn
from sys import argv
from pkg_resources import get_distribution
version = "v" + get_distribution('manta').version

logo = f"""
\033[96m               (\.-./)
\033[96m               /     \\
\033[96m             .'   :   '.
\033[96m        _.-'`     '     `'-._       \033[34;49;1m | \033[34;49;1m Manta {version} \033[00m
\033[96m     .-'          :          '-.    \033[34;49;1m | \033[34;49;3m An In-Situ Debugging Tool for Programmable Hardware \033[00m
\033[96m   ,'_.._         .         _.._',  \033[34;49;1m | \033[34;49m https://github.com/fischermoseley/manta \033[00m
\033[96m   '`    `'-.     '     .-'`
\033[96m             '.   :   .'            \033[34;49;1m | \033[34;49;3m Originally created by Fischer Moseley \033[00m
\033[96m               \_. ._/
\033[96m         \       |^|
\033[96m          |      | ;
\033[96m          \\'.___.' /
\033[96m           '-....-'  \033[00m

Supported commands:
    gen      [config_file] [verilog_file]                           generate a verilog file specifying the Manta module from a given configuration file, and save to the provided path
    capture  [config_file] [la_core_name] [vcd_file] [verilog_file] start a capture on the specified core, and save the results to a .vcd or .v file at the provided path(s)
    ports                                                           list all available serial ports
    help, ray                                                       display this splash screen (hehe...splash screen)
"""

def help():
    print(logo)


def wrong_args():
    raise ValueError('Wrong number of arguments, run "manta help" for usage.')


def gen(config_path, output_path):
    m = Manta(config_path)

    from amaranth.back import verilog

    with open(output_path, "w") as f:
        f.write(
            verilog.convert(
                m,
                name="manta",
                ports=m.get_top_level_ports(),
                strip_internal_attrs=True,
            )
        )


def capture(config_path, logic_analyzer_name, export_paths):
    m = Manta(config_path)
    la = getattr(s, logic_analyzer_name)
    cap = la.capture()

    for path in export_paths:
        if ".vcd" in path:
            cap.export_vcd(path)
        elif ".v" in path:
            cap.export_playback_verilog(path)
        else:
            warn(f"Unrecognized file type, skipping {path}.")


def mmap(config_path):
    print(Manta(config_path).mmap())


def ports():
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


def main():
    if len(argv) == 1:
        help()

    elif argv[1] in ["help", "-h", "-help", "--help", "ray"]:
        help()

    elif argv[1] == "gen":
        if len(argv) != 4:
            wrong_args()
        gen(argv[2], argv[3])

    elif argv[1] == "capture":
        if len(argv) < 5:
            wrong_args()
        capture(argv[2], argv[3], argv[4])

    elif argv[1] == "playback":
        if len(argv) != 5:
            wrong_args()
        playback(argv[2], argv[3], argv[4])

    elif argv[1] == "mmap":
        if len(argv) != 3:
            wrong_args()
        mmap(argv[2])

    elif argv[1] == "ports":
        ports()

    else:
        wrong_args()


if __name__ == "__main__":
    main()
