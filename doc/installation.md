Before installing, make sure to upgrade your `pip` to the latest version:

```bash
pip install --upgrade pip
```

## Latest Version
You can install the latest version of Manta directly from source with:

```bash
pip install --upgrade git+https://github.com/fischermoseley/manta.git
```

## Editable Development Install
If you're working on the source, you might want an editable installation with some extra dependencies used for development:

```bash
git clone https://github.com/fischermoseley/manta.git
cd manta
pip install -e ".[dev]"
```

Manta's hardware-in-the-loop tests rely on Amaranth's build system for programming FPGAs, which in turn rely on the open-source `xc3sprog` and `iceprog` tools for programming Xilinx and ice40 devices, respecitvely. If you'd like to run these tests locally, you may need to install these tools and have them available on your `PATH`. If you're on Linux, you may also need to add a new udev rule to give non-superuser accounts access to any connected FTDI devices. This can be done by making a new file at `/etc/udev/rules.d/99-ftdi-devices.rules`, which contains:

```
ACTION=="add", ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", MODE:="666"
```

Be sure to reload your udev rules after saving the file.

## Adding Manta to Path (Recommended)

It's recommended to place Manta on your system path by adding `export PATH="~/.local/bin:$PATH"` to your `.bashrc` or `.zshrc`. This isn't strictly necessary, but it means that Manta (and any other executable Python modules) can be run as just `manta` on the command line, instead of `python3 -m manta`. If you're on Windows, this location will likely be different.

Later Manta will be availabe on the PyPI lists, and you'll be able to just `pip install mantaray`, but that's not configured quite yet.

## Dependencies
Manta requires the following dependencies:

- [Amaranth HDL](https://amaranth-lang.org/docs/amaranth/latest/), which comes with it's own built-in copy of Yosys.
- [LiteEth](https://github.com/enjoy-digital/liteeth), for sending and receiving UDP packets on the FPGA.
- [pySerial](https://pyserial.readthedocs.io/en/latest/index.html), for communicating with the FPGA over UART.
- [pyYAML](https://pyyaml.org/), for parsing configuration files written in YAML.
- [pyVCD](https://github.com/westerndigitalcorporation/pyvcd), for writing waveforms captured by the Logic Analyzer Core to standard Value Change Dump (VCD) files.

As well as these dependencies for development, which are installed with the `[dev]` argument:

- [Pytest](https://pytest.org/), for unit testing.
- [Black](https://black.readthedocs.io/en/stable/), for formatting the Python source.
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material/), for generating the documentation site.
- [amaranth_boards](https://github.com/amaranth-lang/amaranth-boards), for building designs for hardware-in-the-loop testing done by the CI.
