# Roadmap

## Prior to v1.0.0 release:
_targeting August 2023_

- ~~Clean up UART testbenches, make them actually test things~~
- Pull text from thesis into documentation site
- Add API reference to documentation site
- Port logic analyzer examples to the icestick
    - This requires refactoring the block memory core to use unpacked arrays, since Yosys doesn't support packed arrays.
- Add method for dumping logic analyzer data to Python
- Add clock domain crossing to IO core
- Verify that >16 bit probes work on IO core
- Add clock domain crossing to Logic Analyzer Core
- Verify that capture modes work on the Logic Analyzer Core
- Verify that external triggers work on the Logic Analyzer Core
- Add global AND/OR to Logic Analyzer Core
- Make super super sure everything works (need hardware for that)

## Prior to v1.1.0 release:
- Fix Ethernet packet format
- Switch from Scapy to Python sockets library

## Prior to v1.2.0 release:
- [FuseSoC](https://github.com/fusesoc/fusesoc.github.io) Integration