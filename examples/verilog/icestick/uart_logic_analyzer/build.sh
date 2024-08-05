#!/usr/bin/env bash
set -e

python3 -m manta gen manta.yaml manta.v
$YOSYS -p 'synth_ice40 -top top_level -json top_level.json' top_level.sv
$NEXTPNR_ICE40 --hx1k --json top_level.json --pcf top_level.pcf --asc top_level.asc
$ICEPACK top_level.asc top_level.bin