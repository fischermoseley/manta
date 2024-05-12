## Repository Structure
- `src/manta/` contains the Python source needed to generate and run the cores.
- `test/` contains Manta's tests, which are a mix of functional simulations and hardware-in-the-loop testing. These tests leverage the `pytest` testing framework.
- `doc/` contains the documentation you're reading right now!
- `examples/` contains examples of Manta being used in designs for a handful of FPGA boards.
- `.github/` contains GitHub Actions workflows for automatically running the tests and building the documentation site on every commit.

## Tools Used
- The [YosysHQ](https://github.com/YosysHQ) tools and [Vivado](https://www.xilinx.com/products/design-tools/vivado.html) are used for building bitstreams.
- [draw.io](https://app.diagrams.net/) is used for block diagrams.
- [GitHub Pages](https://pages.github.com/) is used to serve the documentation site, which is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
- [GitHub Actions](https://docs.github.com/en/actions) is used for continuous integration.

## GitHub Actions Setup
Since Vivado is large and requires individual licenses, it is run on a private server, which is configured as a self-hosted runner in GitHub Actions. This is a virtual server hosted with KVM/QEMU and managed by libvirt, which is configured as transient so that it reloads its state from a snapshot periodically. A Nexys4 DDR and Icestick are connected to the physical machine and passthrough-ed to this VM so that continuous integration can check against real hardware.