import os
import tempfile

from manta.cli import gen, inst


def test_verilog_gen():
    with tempfile.TemporaryDirectory() as tmp_dir:
        print("Created temporary directory at", tmp_dir)

        gen("test/test_verilog_gen.yaml", tmp_dir + "/manta.v")

        if not os.path.isfile(tmp_dir + "/manta.v"):
            raise ValueError("No Verilog file generated!")


def test_inst_gen():
    inst_string = inst("test/test_verilog_gen.yaml")

    if not inst_string:
        raise ValueError("No Verilog instantiation generated!")
