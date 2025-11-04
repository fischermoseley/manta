#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=examples/common/find_tool.sh
source "$(dirname "$(readlink -f "$0")")/find_tool.sh"

# Make sure Vivado is accessible
VIVADO_CMD=$(find_tool vivado)

# Generate Verilog source for Manta
python3 -m manta gen manta.yaml manta.v

# Clean build/ directory, and run Vivado from within it
rm -rf build/
mkdir -p build/
cd build
$VIVADO_CMD -mode batch -source ../../../../common/build.tcl
