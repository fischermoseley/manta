test: auto_gen sim formal

examples: icestick nexys_a7

clean:
	rm -f *.out *.vcd
	rm -rf dist/
	rm -rf src/mantaray.egg-info

	rm -rf test/formal_verification/*_basic
	rm -rf test/formal_verification/*_cover

	rm -f examples/nexys_a7/io_core/obj/*
	rm -f examples/nexys_a7/io_core/src/manta.v

	rm -f examples/nexys_a7/logic_analyzer/obj/*
	rm -f examples/nexys_a7/logic_analyzer/src/manta.v

	rm -f examples/nexys_a7/lut_mem/obj/*
	rm -f examples/nexys_a7/lut_mem/src/manta.v

	rm -f examples/icestick/io_core/*.bin
	rm -f examples/icestick/io_core/manta.v

	rm -f examples/icestick/lut_mem/*.bin
	rm -f examples/icestick/lut_mem/manta.v

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
sim: ethernet_tx_tb ethernet_rx_tb mac_tb block_memory_tb io_core_tb logic_analyzer_tb bridge_rx_tb bridge_tx_tb lut_mem_tb block_memory_tb

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
	manta gen manta.yaml manta.v;								\
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

lut_mem_tb:
	iverilog -g2012 -o sim.out -y src/manta/lut_mem_core test/functional_sim/lut_mem_tb.sv
	vvp sim.out
	rm sim.out

# Formal Verification
formal:
	sby -f test/formal_verification/uart_rx.sby

# Build Examples
nexys_a7: nexys_a7_video_sprite nexys_a7_io_core nexys_a7_ps2_logic_analyzer nexys_a7_lut_mem

nexys_a7_video_sprite:
	cd examples/nexys_a7/video_sprite;	\
	manta gen manta.yaml src/manta.v;	\
	build

nexys_a7_io_core:
	cd examples/nexys_a7/io_core/;   	\
	manta gen manta.yaml manta.v;		\
	build

nexys_a7_ps2_logic_analyzer:
	cd examples/nexys_a7/ps2_logic_analyzer/;  					\
	manta gen manta.yaml src/manta.v;							\
	manta playback manta.yaml my_logic_analyzer sim/playback.v;	\
	build

nexys_a7_lut_mem:
	cd examples/nexys_a7/lut_mem/;   	\
	manta gen manta.yaml manta.v;	\
	build

icestick: icestick_io_core icestick_lut_mem

icestick_io_core:
	cd examples/icestick/io_core/;	\
	manta gen manta.yaml manta.v;  	\
	./build.sh

icestick_lut_mem:
	cd examples/icestick/lut_mem/; 	\
	manta gen manta.yaml manta.v;  	\
	./build.sh