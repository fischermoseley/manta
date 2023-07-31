VIVADO_PATH=/tools/Xilinx/Vivado/2023.1/bin/vivado

test: auto_gen sim formal

examples: icestick nexys_a7

clean:
	rm *.out *.vcd
	rm **/lab-bc.py
	rm -rf dist/
	rm -rf src/mantaray.egg-info

	rm -rf test/formal_verification/*_basic
	rm -rf test/formal_verification/*_cover

	rm -f examples/nexys_a7/*/obj/*
	rm -f examples/nexys_a7/*/src/manta.v

	rm -f examples/icestick/*/*.bin
	rm -f examples/icestick/*/manta.v

serve_docs:
	mkdocs serve

total_loc:
	find . -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.yml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l

real_loc:
	find src test -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l

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
	iverilog -g2012 -o sim.out -y src/manta			\
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

# Formal Verification
formal:
	sby -f test/formal_verification/uart_rx.sby
	sby -f test/formal_verification/bridge_rx.sby

# Build Examples
NEXYS_A7_EXAMPLES := io_core_ether io_core_uart ps2_logic_analyzer video_sprite_ether video_sprite_uart
ICESTICK_EXAMPLES := io_core

.PHONY: nexys_a7 $(NEXYS_A7_EXAMPLES)
nexys_a7: $(NEXYS_A7_EXAMPLES)

$(NEXYS_A7_EXAMPLES):
	cd examples/nexys_a7/$(NEXYS_A7_EXAMPLES)
	python3 -m manta gen manta.yaml src/manta.v; \
	rm -rf obj; \
	mkdir -p obj; \
	$(VIVADO_PATH) -mode batch -source ../build.tcl

icestick: $(ICESTICK_EXAMPLES)

$(ICESTICK_EXAMPLES):
	cd examples/icestick/$(ICESTICK_EXAMPLES); \
	python3 -m manta gen manta.yaml manta.v; \
	../build.sh
