build: 
	python3 -m build

pypi_upload: build
	python3 -m twine upload --repository testpypi dist/*	

lint:
	python3 -m black src/manta/__init__.py
	python3 -m black src/manta/__main__.py

serve_docs:
	mkdocs serve

total_loc:
	find . -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.yml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l

real_loc:
	find src ${TB} -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l

test: api_gen func_sim

# API Generation Tests
api_gen: 
	python3 test/api_gen/run_test.py

# Functional Simulation
func_sim: io_core_tb logic_analyzer_tb bit_fifo_tb bridge_rx_tb bridge_tx_tb fifo_tb lut_ram_tb uart_tb uart_tx_tb 

io_core_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/io_core_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

logic_analyzer_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/logic_analyzer_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

bit_fifo_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/bit_fifo_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

bridge_rx_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/bridge_rx_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

bridge_tx_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/bridge_tx_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

fifo_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/fifo_tb.sv -y src/manta 
	vvp sim.out >> /dev/null # this one is noisy right now
	rm sim.out

lut_ram_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/lut_ram_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

uart_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/uart_tb.sv -y src/manta
	vvp sim.out
	rm sim.out

uart_tx_tb:
	iverilog -g2012 -o sim.out test/hdl_tb/uart_tx_tb.sv -y src/manta
	vvp sim.out
	rm sim.out
	
clean:
	rm -f *.out *.vcd
	rm -rf dist/
	rm -rf src/mantaray.egg-info
