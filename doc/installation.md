## Latest Release (Recommended)
The latest release of Manta can be installed from [PyPI](https://pypi.org/project/manta-fpga/) with:

```bash
pip install --upgrade manta-fpga
```

## Development Snapshot
The latest development snapshot of Manta can be installed with:

```bash
pip install --upgrade git+https://github.com/fischermoseley/manta.git
```

The commands above reference pip, but if your project uses an alternative Python package manager like uv, Poetry, or PDM, then consult your tool's documentation for installation instructions.

It's recommended to install Manta into a virtual environment instead of your system Python. Among the many other benefits virtual environments offer, this will conveniently add the `manta` executable to your PATH when the virtual environment is active. This allows you to invoke the tool with `manta`, rather than the more verbose `python3 -m manta`.

## Editable Development Install
This project uses the [uv](https://docs.astral.sh/uv/) package manager, which will need to be installed before working with the source. The following commands will create a venv with an editable installation of `manta`, along with some extra tools used for development:

```bash
git clone https://github.com/fischermoseley/manta.git
cd manta
uv sync
uv run pre-commit install
source .venv/bin/activate # optional, but convenient!
```

## Running Tests
Manta is verified with a combination of functional simulation and hardware-in-the-loop tests. The functional simulation uses Amaranth's built-in simulator, and can be run with no additional hardware or tools. However, the hardware tests target the following boards and thus require the tools below:

- *Digilent Nexys4DDR:* AMD/Xilinx Vivado, `xc3sprog`
- *Lattice iCEstick:* yosys, nextpnr-ice40, icepack, iceprog. Easily installable from `oss-cad-suite`.

Hardware tests targeting a given board will be skipped unless the required tools are available on your `PATH` or are referenced via environment variable. See `.env` for an example.

The tests may be invoked with `make test`, which will run both the simulation testbenches and the hardware-in-the-loop tests.

### udev Rules (for Linux users)

If you're on Linux, you may also need to add a new udev rule to give non-superuser accounts access to any connected FTDI devices. This can be done by making a new file at `/etc/udev/rules.d/99-ftdi-devices.rules`, which contains:

```
ACTION=="add", ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", MODE:="666"
```

Be sure to reload your udev rules after saving the file. On most distributions, this is accomplished with:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```
