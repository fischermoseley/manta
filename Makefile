# Tool Paths
VIVADO=/tools/Xilinx/Vivado/2023.1/bin/vivado
YOSYS=/tools/oss-cad-suite/bin/yosys
NEXTPNR_ICE40=/tools/oss-cad-suite/bin/nextpnr-ice40
ICEPACK=/tools/oss-cad-suite/bin/icepack

test: auto_gen sim formal

examples: icestick nexys_a7

clean:
	@echo "Deleting everything matched by .gitignore"
	git clean -Xdf

serve_docs:
	mkdocs serve

# Python Operations
python_build:
	python3 -m build

pypi_upload: build
	python3 -m twine upload --repository testpypi dist/*

python_lint:
	python3 -m black src/manta/__init__.py
	python3 -m black src/manta/__main__.py

# API Generation Tests
auto_gen:
	python3 test/auto_gen/run_tests.py

# Build Examples
NEXYS_A7_EXAMPLES := io_core_ether io_core_uart ps2_logic_analyzer video_sprite_ether video_sprite_uart block_mem_uart logic_analyzer_uart

.PHONY: nexys_a7 $(NEXYS_A7_EXAMPLES)
nexys_a7: $(NEXYS_A7_EXAMPLES)

$(NEXYS_A7_EXAMPLES):
	cd examples/nexys_a7/$@; \
	python3 -m manta gen manta.yaml src/manta.v; \
	rm -rf obj; \
	mkdir -p obj; \
	$(VIVADO) -mode batch \
		-source ../build.tcl \
		-log obj/build.log \
		-jou obj/build.jou; \
	rm -rf .Xil;

ICESTICK_EXAMPLES := io_core

.PHONY: icestick $(ICESTICK_EXAMPLES)
icestick: $(ICESTICK_EXAMPLES)

$(ICESTICK_EXAMPLES):
	cd examples/icestick/$@; \
	python3 -m manta gen manta.yaml manta.v; \
	$(YOSYS) -p 'synth_ice40 -top top_level -json top_level.json' top_level.sv; \
	$(NEXTPNR_ICE40) --hx1k --json top_level.json --pcf top_level.pcf --asc top_level.asc; \
	$(ICEPACK) top_level.asc top_level.bin; \
	rm -f *.json; \
	rm -f *.asc;

# Formal Verification
formal:
	sby -f test/formal_verification/bridge_rx.sby

# Functional Simulation
sim: ethernet_tx_tb ethernet_rx_tb mac_tb block_memory_tb io_core_tb logic_analyzer_tb bridge_rx_tb bridge_tx_tb block_memory_tb

ethernet_tx_tb:
	iverilog -g2012 -o sim.out -y src/manta/ether_iface test/functional_sim/ethernet_tx_tb.sv
	vvp sim.out
	rm sim.out

ethernet_rx_tb:
	iverilog -g2012 -o sim.out -y src/manta/ether_iface test/functional_sim/ethernet_rx_tb.sv
	vvp sim.out
	rm sim.out

mac_tb:
	iverilog -g2012 -o sim.out -y src/manta/ether_iface test/functional_sim/mac_tb.sv
	vvp sim.out
	rm sim.out

block_memory_tb:
	iverilog -g2012 -o sim.out -y src/manta/block_mem_core test/functional_sim/block_memory_tb.sv
	vvp sim.out
	rm sim.out

io_core_tb:
	iverilog -g2012 -o sim.out 						\
	test/functional_sim/io_core_tb/io_core_tb.sv	\
	test/functional_sim/io_core_tb/io_core.v
	vvp sim.out
	rm sim.out

logic_analyzer_tb:
	cd test/functional_sim/logic_analyzer_tb;					\
	python3 -m manta gen manta.yaml manta.v;					\
	iverilog -g2012 -o sim.out logic_analyzer_tb.sv manta.v;	\
	vvp sim.out; 												\
	rm sim.out

bridge_rx_tb:
	iverilog -g2012 -o sim.out -y src/manta/uart_iface test/functional_sim/bridge_rx_tb.sv
	vvp sim.out
	rm sim.out

bridge_tx_tb:
	iverilog -g2012 -o sim.out -y src/manta/uart_iface test/functional_sim/bridge_tx_tb.sv
	vvp sim.out
	rm sim.out

uart_rx_tb:
	iverilog -g2012 -o sim.out -y src/manta/uart_iface test/functional_sim/uart_rx_tb.sv
	vvp sim.out
	rm sim.out

uart_tx_tb:
	iverilog -g2012 -o sim.out -y src/manta/uart_iface test/functional_sim/uart_tx_tb.sv
	vvp sim.out
	rm sim.out
