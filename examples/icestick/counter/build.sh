#!/bin/bash
yosys -p 'synth_ice40 -top top_level -json counter.json' src/top_level.sv
nextpnr-ice40 --hx1k --json counter.json --pcf pcf/top_level.pcf --asc counter.asc
icepack counter.asc counter.bin