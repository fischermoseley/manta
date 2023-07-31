#!/bin/bash
yosys -p 'synth_ice40 -top top_level -json top_level.json' top_level.sv
nextpnr-ice40 --hx1k --json top_level.json --pcf top_level.pcf --asc top_level.asc
icepack top_level.asc top_level.bin
rm -f *.json
rm -f *.asc