`default_nettype none

`timescale 1ns / 1ps

module uart_tx_tb();
	logic clk;
	logic rst;
	logic [7:0] data;
	logic start;
	logic busy;
	logic txd;


	uart_tx #(
		.DATA_WIDTH(8),
		.CLK_FREQ_HZ(100_000_000),
		.BAUDRATE(115200)) 
		uut (
		.clk(clk),
		.rst(rst),
		.data(data),
		.start(start),

		.busy(busy),
		.txd(txd));

  	always begin
    		#5;
    		clk = !clk;
  	end

  	initial begin
    		$dumpfile("uart_tx.vcd");
    		$dumpvars(0, uart_tx_tb);
		clk = 0;
		rst = 1;
		start = 0;
		#10;
		rst = 0;
		data = 'h0F;
		#10;
		start = 1;
		#10;
		start = 0;
		#150000;
		$finish();
	end
endmodule

`default_nettype wire
