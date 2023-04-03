`default_nettype none
`timescale 1ns / 1ps

module fifo_tb();
	logic clk;
	logic rst;

	logic [7:0] in;
	logic in_valid;
	
	logic out_req;
	logic [7:0] out;

	logic [11:0] size;
	logic empty;
	logic full;

	fifo uut (
		.clk(clk),
		.bram_rst(rst),
	
		.in(in),
		.in_valid(in_valid),
		
		.out_req(out_req),
		.out(out),

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
		in = 0;
		in_valid = 0;
		out_req = 0;
		#10;
		rst = 0;
		#10;

		// try and load some data, make sure counter increases
		in_valid = 1;

		for(int i=0; i < 4097; i++) begin
			in = i;
			#10;
		end
		
		in_valid = 0;

		// try and read out said data
		out_req = 1;
		for(int i=0; i < 4097; i++) begin
			$display("%h", out);
			#10;
		end

		$finish();
	end
endmodule

`default_nettype wire
