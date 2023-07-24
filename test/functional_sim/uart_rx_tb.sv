`default_nettype none

`define CP 10
`define HCP 5

task automatic test_receive (
	input [7:0] data,
	input integer CLOCKS_PER_BAUD
	);

	// send a byte to uart_rx, and check that it receives properly

	integer data_bit = 0;
	logic valid_has_been_asserted = 0;

	for(int i=0; i < (10*CLOCKS_PER_BAUD); i++) begin

		// clock out data bits on each baud period
		data_bit = i / CLOCKS_PER_BAUD;
		if (data_bit == 0) uart_rx_tb.tb_urx_rx = 0;
		else if ((data_bit > 0) && (data_bit < 9)) uart_rx_tb.tb_urx_rx = data[data_bit-1];
		else uart_rx_tb.tb_urx_rx = 1;


		// every cycle, run checks on uart_rx:

		// make sure valid isn't asserted before end of byte
		if (data_bit < 9) begin
			assert(uart_rx_tb.urx_tb_valid == 0) else $fatal(0, "valid asserted before end of byte!");
		end

		// make sure valid is only asserted once
		if (valid_has_been_asserted) begin
			assert(uart_rx_tb.urx_tb_valid == 0) else $fatal(0, "valid asserted more than once!");
		end

		// make sure byte is presented once last bit has been clocked out
		if (uart_rx_tb.urx_tb_valid) begin
			assert(data_bit == 9) else $fatal(0, "byte presented before it is complete");
			assert(uart_rx_tb.urx_tb_data == data) else $fatal(0, "wrong data!");
			valid_has_been_asserted = 1;
		end

		#`CP;
	end

	// make sure valid was asserted at some point
	assert (valid_has_been_asserted) else $fatal(0, "valid not asserted!");
endtask

module uart_rx_tb();
	logic clk;
	integer test_num;

	logic tb_urx_rx;
	logic [7:0] urx_tb_data;
	logic urx_tb_valid;
	uart_rx #(.CLOCKS_PER_BAUD(10)) urx (
		.clk(clk),
		.rx(tb_urx_rx),
		.data_o(urx_tb_data),
		.valid_o(urx_tb_valid));

  	always begin
    	#`HCP
    	clk = !clk;
  	end

  	initial begin
    	$dumpfile("uart_rx_tb.vcd");
    	$dumpvars(0, uart_rx_tb);
		clk = 0;
		test_num = 0;
		tb_urx_rx = 1;
		#`HCP;

		// test all possible bytes
		test_num = test_num + 1;
		for(int i=0; i < 256; i++) begin
			test_receive(i, 10);
			#(100*`CP);
		end

		// test all possible bytes (no delay between them)
		test_num = test_num + 1;
		for(int i=0; i < 256; i++) begin
			test_receive(i, 10);
		end

		$finish();
	end
endmodule

`default_nettype wire
