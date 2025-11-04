#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=examples/common/find_tool.sh
source "$(dirname "$(readlink -f "$0")")/find_tool.sh"

# Make sure tools are accessible
YOSYS_CMD=$(find_tool yosys)
NEXTPNR_ICE40_CMD=$(find_tool nextpnr-ice40)
ICEPACK_CMD=$(find_tool icepack)

# Generate Verilog source for Manta
python3 -m manta gen manta.yaml manta.v

# Clean build/ directory, and run tools from within it
rm -rf build/
mkdir -p build/
cd build
$YOSYS_CMD -p 'synth_ice40 -top top_level -json top_level.json' ../top_level.sv
$NEXTPNR_ICE40_CMD --hx1k --json top_level.json --pcf ../top_level.pcf --asc top_level.asc
$ICEPACK_CMD top_level.asc top_level.bin
