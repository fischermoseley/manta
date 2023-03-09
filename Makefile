build: 
	python3 -m build

pypi_upload: build
	python3 -m twine upload --repository testpypi dist/*	

lint:
	python3 -m black src/manta/__init__.py
	python3 -m black src/manta/__main__.py

sim: sim_bit_fifo sim_bridge_rx sim_bridge_tx fifo_tb lut_mem_tb uart_tx_tb

sim_bit_fifo:
	iverilog -g2012 -o sim.out test/bit_fifo_tb.sv src/manta/bit_fifo.v
	vvp sim.out
	rm sim.out

sim_bridge_rx:
	iverilog -g2012 -o sim.out test/bridge_rx_tb.sv src/manta/bridge_rx.v
	vvp sim.out
	rm sim.out

sim_bridge_tx:
	iverilog -g2012 -o sim.out test/bridge_tx_tb.sv src/manta/bridge_tx.v src/manta/uart_tx.v
	vvp sim.out
	rm sim.out

fifo_tb:
	iverilog -g2012 -o sim.out test/fifo_tb.sv src/manta/fifo.v src/manta/xilinx_true_dual_port_read_first_2_clock_ram.v
	vvp sim.out >> /dev/null # this one is noisy right now
	rm sim.out

lut_mem_tb:
	iverilog -g2012 -o sim.out test/lut_mem_tb.sv src/manta/lut_mem.v 
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

loc:
	find . -type f \( -iname \*.sv -o -iname \*.v -o -iname \*.py -o -iname \*.yaml -o -iname \*.md \) | sed 's/.*/"&"/' | xargs  wc -l