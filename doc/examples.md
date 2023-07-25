Examples can be found under `examples/` in the GitHub repository. These target the following boards:

### Nexys A7/Nexys4 DDR:

- [io_core_ether](https://github.com/fischermoseley/manta/tree/main/examples/nexys_a7/io_core_ether) and [io_core_uart](https://github.com/fischermoseley/manta/tree/main/examples/nexys_a7/io_core_uart)
    - These both demonstrate the IO core, connected to a host machine over either UART or Ethernet. This includes a Manta configuration that's synthesized onto the FPGA, and a script run on the host. This script uses Manta's Python API to draw a pattern on the Nexys A7's built-in LED display, and also report the status of the onboard buttons and switches to the user.

- [ps2_logic_analyzer](https://github.com/fischermoseley/manta/tree/main/examples/nexys_a7/ps2_logic_analyzer)
    -

- [video_sprite_ether] and [video_sprite_uart]

### Icestick

- [io_core](https://github.com/fischermoseley/manta/tree/main/examples/icestick/io_core)