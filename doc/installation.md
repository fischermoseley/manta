## Dependencies
Manta requires the following dependencies:

- pyYAML, which is used for parsing configuration files written in YAML.
- pySerial, used for communicating with the FPGA over UART.
- Scapy, used for communicating with FPGA over Ethernet.
- pyVCD, used for writing waveforms captured by the Logic Analyzer Core to standard Value Change Dump (VCD) files.

All of these dependencies are technically optional. If you're comfortable writing configuration files in JSON, then you don't need pyYAML. If you're using UART exclusively in your project, then you won't need Scapy. That said, Manta will try to install (or use an existing copy of) pyYAML, pySerial, and pyVCD during its own installation to cover all use cases.

## Installation
You can install the latest version of Manta directly from source with:

```
pip install git+https://github.com/fischermoseley/manta.git
```

!!! warning "Note for Ubuntu users:"

    If you're on Ubuntu, you'll probably need to run this first to dodge
    a bug in the current version of Python's `setuptools`:
    ```
    export DEB_PYTHON_INSTALL_LAYOUT=deb_system
    ```
    Do this before installing Manta. If you've already installed it, just
    uninstall, run the above command, and then reinstall.

It's recommended to place Manta on your system path by adding `export PATH="~/.local/bin:$PATH"` to your `.bashrc` or `.zshrc`. This isn't strictly necessary, but it means that Manta (and any other executable Python modules) can be run as just `manta` on the command line, instead of `python3 -m manta`. If you're on Windows, this location will likely be different.

Feel free to install Manta within a virtual environment (venv, Conda, and so on) if you'd like!

Later Manta will be availabe on the PyPI lists, and you'll be able to just `pip install mantaray`, but that's not configured quite yet.