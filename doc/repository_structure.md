## Repository Structure
- `src/manta/` contains the Python and Verilog source needed to generate and run the cores.
- `test/` contains testbenchs for HDL. Manta is written in Verilog 2001, but the testbenches are written in SystemVerilog 2012. These are simulated using Icarus Verilog, which produces `.vcd` files, viewable with your favorite waveform viewer, like GTKWave.
- `doc/` contains the documentation you're reading right now! It's built into a nice static site by Material for MkDocs, which automatically rebuilds the site on every commit to `main`. This is done with a GitHub Action configured in `.github/`
- `examples/` is exactly what it sounds like. It contains examples for both the Digilent Nexys 4 DDR/Nexys A7 with thier onboard Series-7, as well as the Icestick with its onboard iCE40.
- `.github/` also contains some GitHub Actions configuration for automatically running the SystemVerilog testbenches and building the examples, in addition to automatically rebuilding the site.

## Tools Used
- The [YosysHQ](https://github.com/YosysHQ) tools and [Vivado](https://www.xilinx.com/products/design-tools/vivado.html) are used for building bitstreams.
- [Wavedrom](https://wavedrom.com/) is used for for waveform diagrams, and [draw.io](https://app.diagrams.net/) for block diagrams
- [GitHub Pages](https://pages.github.com/) is used to serve the documentation site, which is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
- [GitHub Actions](https://docs.github.com/en/actions) is used for continuous integration.

## GitHub Actions Setup
Since Vivado is large and requires individual licenses it's run on a private server, which is configured as a self-hosted runner in GitHub Actions. This is a virtual server hosted with KVM/QEMU and managed by libvirt, which is configured as transient so that it reloads its state from a snapshot periodically. A Nexys A7 and Icestick are connected to the physical machine and passthrough-ed to this VM so that continuous integration can check against real hardware.