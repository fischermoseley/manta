`default_nettype none
`timescale 1ns / 1ps

`define CP 10
`define HCP 5

module uart_tx_tb();
	logic clk;

	logic [7:0] tb_utx_data;
	logic tb_utx_valid;
	logic utx_tb_busy;

	logic utx_tb_tx;

	uart_tx #(.CLOCKS_PER_BAUD(10)) utx (
		.clk(clk),

		.data(tb_utx_data),
		.valid(tb_utx_valid),
		.busy(utx_tb_busy),

		.tx(utx_tb_tx));


	logic zcpu_tb_tx; 
	logic zcpu_tb_busy;
	
	tx_uart #(.CLOCKS_PER_BAUD(10)) zcpu_utx (
		.i_clk(clk),

		.i_wr(tb_utx_valid),
		.i_data(tb_utx_data),
		
		.o_uart_tx(zcpu_tb_tx),
		.o_busy(zcpu_tb_busy));

	logic zcpu_urx_valid;
	logic[7:0] zcpu_urx_data;

	rx_uart #(.CLOCKS_PER_BAUD(10)) zcpu_urx (
		.i_clk(clk),

		.i_uart_rx(utx_tb_tx),
		.o_wr(zcpu_urx_valid),
		.o_data(zcpu_urx_data));

  	always begin
    		#`HCP
    		clk = !clk;
  	end

  	initial begin
		$dumpfile("uart_tx.vcd");
		$dumpvars(0, uart_tx_tb);
		clk = 0;
		tb_utx_data = 0;
		tb_utx_valid = 0;
		#`HCP;

		#(10*`CP);

		$display("send a byte");
		tb_utx_data = 8'h69;
		tb_utx_valid = 1;
		#`CP;
		tb_utx_valid = 0;

		#(150*`CP);

		$display("send another byte");
		tb_utx_data = 8'h42;
		tb_utx_valid = 1;
		#`CP;
		tb_utx_valid = 0;

		#(150*`CP);

		$display("send two bytes back to back");
		tb_utx_data = 8'h69;
		tb_utx_valid = 1;
		#`CP;
		tb_utx_valid = 0;

		#(99*`CP);
		
		tb_utx_data = 8'h42;
		tb_utx_valid = 1;
		#`CP;
		tb_utx_valid = 0;

		#(150*`CP);

		$display("send two bytes back to back, but keep valid asserted");
		tb_utx_data = 8'h69;
		tb_utx_valid = 1;
		#`CP;

		#(99*`CP);
		
		tb_utx_data = 8'h42;
		tb_utx_valid = 1;
		#`CP;
		tb_utx_valid = 0;

		#(150*`CP);

		$finish();
	end
endmodule

`default_nettype wire
