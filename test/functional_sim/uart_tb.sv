`default_nettype none
`timescale 1ns / 1ps

module uart_tb();
	logic clk;
	logic rst;

	logic [7:0] tx_data;
	logic tx_start;

	// transmitters
	logic tx_done_manta;
	logic txd_manta;
	uart_tx #(.CLOCKS_PER_BAUD(10)) tx_manta (
		.clk(clk),

		.data_i(tx_data),
		.start_i(tx_start),
		.done_o(tx_done_manta),

		.tx(txd_manta));

	logic tx_busy_zipcpu;
	logic tx_done_zipcpu;
	logic txd_zipcpu;
	assign tx_done_zipcpu = ~tx_busy_zipcpu;
	tx_uart #(.CLOCKS_PER_BAUD(10)) tx_zipcpu (
		.i_clk(clk),

		.i_wr(tx_start),
		.i_data(tx_data),
		.o_uart_tx(txd_zipcpu),
		.o_busy(tx_busy_zipcpu));

	// receivers
	logic [7:0] rx_data_manta;
	logic rx_valid_manta;
	uart_rx #(.CLOCKS_PER_BAUD(10)) rx_manta (
		.clk(clk),
		.rx(txd_manta),
		.data_o(rx_data_manta),
		.valid_o(rx_valid_manta));

	logic [7:0] rx_data_zipcpu;
	logic rx_valid_zipcpu;
	rx_uart #(.CLOCKS_PER_BAUD(10)) rx_zipcpu (
		.i_clk(clk),
		.i_uart_rx(txd_zipcpu),
		.o_wr(rx_valid_zipcpu),
		.o_data(rx_data_zipcpu));

  	always begin
    		#5;
    		clk = !clk;
  	end

  	initial begin
    	$dumpfile("uart.vcd");
    	$dumpvars(0, uart_tb);
		clk = 0;

		tx_data = 'hFF;
		tx_start = 0;
		#10;
		rst = 0;
		#10;
		tx_start = 1;
		#10;
		tx_start = 0;
		#10000;

		// send another byte!
		tx_data = 'b0100_1101;
		tx_start = 1;
		#3000;
		tx_start = 0;
		#10000;

		$finish();
	end
endmodule

`default_nettype wire
