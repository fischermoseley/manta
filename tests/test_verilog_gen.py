from manta.cli import gen, inst

CONFIG_FILE = "test/test_verilog_gen.yaml"


def test_verilog_gen(tmp_path):
    output_path = tmp_path / "manta.v"

    gen(CONFIG_FILE, output_path)
    assert output_path.is_file(), "No Verilog file generated!"


def test_inst_gen():
    assert inst(CONFIG_FILE), "No Verilog instantiation generated!"
