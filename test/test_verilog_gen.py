from manta.cli import gen
from manta import Manta
import tempfile
import os


def test_verilog_gen():
    with tempfile.TemporaryDirectory() as tmp_dir:
        print("Created temporary directory at", tmp_dir)

        gen("test/test_verilog_gen.yaml", tmp_dir + "/manta.v")

        if not os.path.isfile(tmp_dir + "/manta.v"):
            raise ValueError("No Verilog file generated!")
