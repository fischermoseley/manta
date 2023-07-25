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