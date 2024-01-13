Before installing, make sure to upgrade your `pip` to the latest version:

```
pip install --upgrade pip
```

## Latest Version
You can install the latest version of Manta directly from source with:

```
pip install --upgrade git+https://github.com/fischermoseley/manta.git
```

## Editable Development Install
If you're working on the source, you might want an editable installation with some extra dependencies used for development:

```
git clone https://github.com/fischermoseley/manta.git
cd manta
pip install -e ".[dev]"
```

## Adding Manta to Path (Recommended)

It's recommended to place Manta on your system path by adding `export PATH="~/.local/bin:$PATH"` to your `.bashrc` or `.zshrc`. This isn't strictly necessary, but it means that Manta (and any other executable Python modules) can be run as just `manta` on the command line, instead of `python3 -m manta`. If you're on Windows, this location will likely be different.

Later Manta will be availabe on the PyPI lists, and you'll be able to just `pip install mantaray`, but that's not configured quite yet.

## Dependencies
Manta requires the following dependencies:

- Amaranth HDL, which comes with it's own built-in copy of Yosys.
- pyYAML, which is used for parsing configuration files written in YAML.
- pySerial, used for communicating with the FPGA over UART.
- pyVCD, used for writing waveforms captured by the Logic Analyzer Core to standard Value Change Dump (VCD) files.

As well as these dependencies for development, which are installed with the `[dev]` argument:

- Pytest, for testing.
- Black, used for formatting the Python source.
- mkdocs-material, for generating the documentation site.
- amaranth_boards, for building designs for hardware-in-the-loop testing done by the CI.
