Before installing, make sure to upgrade your `pip` to the latest version:

```bash
pip install --upgrade pip
```

## Latest Release (Recommended)
The latest release of Manta can be installed from PyPI with:

```bash
pip install --upgrade manta-python
```

## Development Snapshot
The latest development snapshot of Manta can be installed with:

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

Manta's hardware-in-the-loop tests rely on Amaranth's build system for programming FPGAs, which in turn rely on the open-source `xc3sprog` and `iceprog` tools for programming Xilinx and ice40 devices, respecitvely. If you'd like to run these tests locally, you may need to install these tools and have them available on your `PATH`.

If you're on Linux, you may also need to add a new udev rule to give non-superuser accounts access to any connected FTDI devices. This can be done by making a new file at `/etc/udev/rules.d/99-ftdi-devices.rules`, which contains:

```
ACTION=="add", ATTR{idVendor}=="0403", ATTR{idProduct}=="6010", MODE:="666"
```

Be sure to reload your udev rules after saving the file. On most distributions, this is accomplished with:

```bash
udevadm control --reload-rules && udevadm trigger
```

## Adding Manta to PATH (Optional)

Although optional, it is convenient to add the `manta` executable to your system's path. This allows you to invoke Manta's CLI with `manta`, rather than the more verbose `python3 -m manta`. The location of this executable depends on both your platform and if you're using a virtual environment. For example:

- Windows: `%APPDATA%\Python\Scripts`, or `path\to\venv\Scripts` if using a virtual environment.

- macOS/Linux/BSD: `$HOME/.local/bin`, or `path\to\venv\bin` if using a virtual environment.

This also adds any other Python scripts exposed by your installed packages to your PATH.