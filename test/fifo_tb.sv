`default_nettype none
`timescale 1ns / 1ps

module fifo_tb();
	logic clk;
	logic rst;

	logic [7:0] data_in;
	logic input_ready;
	
	logic request_output;
	logic [7:0] data_out;

	logic [11:0] size;
	logic empty;
	logic full;

	fifo uut (
		.clk(clk),
		.rst(rst),
	
		.data_in(data_in),
		.input_ready(input_ready),
		
		.request_output(request_output),
		.data_out(data_out),

		.size(size),
		.empty(empty),
		.full(full));

  	always begin
    		#5;
    		clk = !clk;
  	end

  	initial begin
    		$dumpfile("fifo.vcd");
    		$dumpvars(0, fifo_tb);
		clk = 0;
		rst = 1;
		data_in = 0;
		input_ready = 0;
		request_output = 0;
		#10;
		rst = 0;
		#10;

		// try and load some data, make sure counter increases
		input_ready = 1;

		for(int i=0; i < 4097; i++) begin
			data_in = i;
			#10;
		end
		
		input_ready = 0;

		// try and read out said data
		request_output = 1;
		for(int i=0; i < 4097; i++) begin
			$display("%h", data_out);
			#10;
		end

		$finish();
	end
endmodule

`default_nettype wire
