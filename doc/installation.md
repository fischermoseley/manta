## Installation

You can install the latest version of Manta directly from source with:

```
pip install git+https://github.com/fischermoseley/manta.git
```

If you're on Ubuntu, you'll probably need to run this first to dodge a bug in the current version of Python's `setuptools`:
```
export DEB_PYTHON_INSTALL_LAYOUT=deb_system
```

And go ahead and throw Manta on your system path by adding the following to your `.bashrc` or `.zshrc`.

```
export PATH="~/.local/bin:$PATH"
```
This makes it so that you can run `manta` as it's own command on the command line, instead of having to do `python3 -m manta`.

Later Manta will be availabe on the PyPI lists, and you'll be able to just `pip install mantaray`, but that's not configured quite yet.

## Examples
Examples can be found under `examples/`. These target the Xilinx Series 7 FPGAs on the [Nexys A7](https://digilent.com/reference/programmable-logic/nexys-a7/start)/[Nexys4 DDR](https://digilent.com/reference/programmable-logic/nexys-4-ddr/start) and the Lattice iCE40 on the [Icestick](https://www.latticesemi.com/icestick).