build: 
	python3 -m build

pypi_upload: build
	python3 -m twine upload --repository testpypi dist/*	

lint:
	python3 -m black src/manta/__init__.py
	python3 -m black src/manta/__main__.py

sim: io_core_tb logic_analyzer_tb bit_fifo_tb bridge_rx_tb bridge_tx_tb fifo_tb lut_ram_tb uart_tb uart_tx_tb 

io_core_tb:
	iverilog -g2012 -o sim.out test/io_core_tb.sv src/manta/io_core.v
	vvp sim.out
	rm sim.out

logic_analyzer_tb:
	iverilog -g2012 -o sim.out test/logic_analyzer_tb.sv src/manta/logic_analyzer.v src/manta/la_fsm.v src/manta/trigger_block.v src/manta/trigger.v src/manta/sample_mem.v src/manta/xilinx_true_dual_port_read_first_2_clock_ram.v
	vvp sim.out
	rm sim.out

bit_fifo_tb:
	iverilog -g2012 -o sim.out test/bit_fifo_tb.sv src/manta/bit_fifo.v
	vvp sim.out
	rm sim.out

bridge_rx_tb:
	iverilog -g2012 -o sim.out test/bridge_rx_tb.sv src/manta/bridge_rx.v
	vvp sim.out
	rm sim.out

bridge_tx_tb:
	iverilog -g2012 -o sim.out test/bridge_tx_tb.sv src/manta/bridge_tx.v src/manta/uart_tx.v
	vvp sim.out
	rm sim.out

fifo_tb:
	iverilog -g2012 -o sim.out test/fifo_tb.sv src/manta/fifo.v src/manta/xilinx_true_dual_port_read_first_2_clock_ram.v
	vvp sim.out >> /dev/null # this one is noisy right now
	rm sim.out

lut_ram_tb:
	iverilog -g2012 -o sim.out test/lut_ram_tb.sv src/manta/lut_ram.v 
	vvp sim.out
	rm sim.out

uart_tb:
	iverilog -g2012 -o sim.out test/uart_tb.sv src/manta/tx_uart.v src/manta/uart_rx.v 
	vvp sim.out
	rm sim.out

uart_tx_tb:
	iverilog -g2012 -o sim.out test/uart_tx_tb.sv src/manta/tx_uart.v src/manta/uart_tx.v src/manta/rx_uart.v 
	vvp sim.out
	rm sim.out
	
clean:
	rm -f *.out *.vcd
	rm -rf dist/
	rm -rf src/mantaray.egg-info

total_loc:
	find . -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.yml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l

real_loc:
	find src test -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l