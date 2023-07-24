`default_nettype none

`define CP 10
`define HCP 5

task automatic transmit_byte (
	input [7:0] data,
	input integer CLOCKS_PER_BAUD
	);

	// send a byte from uart_tx, and check that it transmits properly

	integer data_bit = 0;
	for(int i=0; i < (10*CLOCKS_PER_BAUD)-1; i++) begin

		// check that data bit is correct on every baud period
		data_bit = i / CLOCKS_PER_BAUD;
		if (data_bit == 0) begin
			assert(uart_tx_tb.utx_tb_tx == 0) else $fatal(0, "wrong start bit!");
		end

		else if ((data_bit > 0) && (data_bit < 9)) begin
			assert(uart_tx_tb.utx_tb_tx == data[data_bit-1]) else $fatal(0, "wrong data bit!");
		end

		else begin
			assert(uart_tx_tb.utx_tb_tx == 1) else $fatal(0, "wrong stop bit!");
		end


		// check that done is not asserted during transmisison
		assert(!uart_tx_tb.utx_tb_done) else $fatal(0, "wrong done!");
		#`CP;
	end

	// assert that done is asserted at end of transmission
	assert(uart_tx_tb.utx_tb_done) else $fatal(0, "wrong done!");
endtask

module uart_tx_tb();
	logic clk;
	integer test_num;

	logic [7:0] tb_utx_data;
	logic tb_utx_start;
	logic utx_tb_done;
	logic utx_tb_tx;

	uart_tx #(.CLOCKS_PER_BAUD(10)) utx (
		.clk(clk),

		.data_i(tb_utx_data),
		.start_i(tb_utx_start),
		.done_o(utx_tb_done),

		.tx(utx_tb_tx));

	always begin
    	#`HCP
    	clk = !clk;
  	end

  	initial begin
		$dumpfile("uart_tx_tb.vcd");
		$dumpvars(0, uart_tx_tb);
		clk = 0;
		test_num = 0;

		tb_utx_data = 0;
		tb_utx_start = 0;
		#`HCP;

		// test all possible bytes
		test_num = test_num + 1;
		for(int i=0; i < 256; i++) begin
			tb_utx_start = 1;
			tb_utx_data = i;
			#`CP;
			tb_utx_start = 0;
			tb_utx_data = 0;
			transmit_byte(i, 10);
			#(100*`CP);
		end

		// test all possible bytes (no delay between them)
		test_num = test_num + 1;
		for(int i=0; i < 256; i++) begin
			tb_utx_start = 1;
			tb_utx_data = i;
			#`CP;
			tb_utx_data = 0;
			transmit_byte(i, 10);
		end

		$finish();
	end
endmodule

`default_nettype wire
