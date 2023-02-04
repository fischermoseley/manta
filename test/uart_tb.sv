`default_nettype none

`timescale 1ns / 1ps

module uart_tb();
	logic clk;
	logic rst;
	logic [7:0] tx_data, rx_data;
	logic tx_start, rx_ready;
	logic tx_busy, rx_busy;
	logic txd;


	uart_tx #(
		.DATA_WIDTH(8),
		.CLK_FREQ_HZ(100_000_000),
		.BAUDRATE(115200))
		tx (
		.clk(clk),
		.rst(rst),
		.data(tx_data),
		.start(tx_start),

		.busy(tx_busy),
		.txd(txd));


	uart_rx #(
		.DATA_WIDTH(8),
		.CLK_FREQ_HZ(100_000_000),
		.BAUDRATE(115200))
		rx (
		.clk(clk),
		.rst(rst),
		.rxd(txd),

		.data(rx_data),
		.ready(rx_ready),
		.busy(rx_busy));

  	always begin
    		#5;
    		clk = !clk;
  	end

  	initial begin
    	$dumpfile("uart.vcd");
    	$dumpvars(0, uart_tb);
		clk = 0;
		rst = 1;
		tx_data = 'h0F;
		tx_start = 0;
		#10;
		rst = 0;
		#10;
		tx_start = 1;
		#10;
		tx_start = 0;
		#150000;

		// send another byte!
		tx_data = 'hBE;
		tx_start = 1;
		#10;
		tx_start = 0;
		#150000;

		$finish();
	end
endmodule

`default_nettype wire
