`default_nettype none
`timescale 1ns / 1ps

module fifo (
	input wire clk,
	input wire bram_rst,

	input wire [WIDTH - 1:0] in,
	input wire in_valid,

	output reg [WIDTH - 1:0] out,
	input wire out_req,
	output reg out_valid,

	output reg [AW:0] size,
	output reg empty,
	output reg full
	);

	parameter WIDTH = 8;
	parameter DEPTH = 4096;
	localparam AW = $clog2(DEPTH);

	reg [AW:0] write_pointer;
	reg [AW:0] read_pointer;

	reg empty_int;
	assign empty_int = (write_pointer[AW] == read_pointer[AW]);

	reg full_or_empty;
	assign full_or_empty = (write_pointer[AW-1:0] == read_pointer[AW-1:0]);

	assign full = full_or_empty & !empty_int;
	assign empty = full_or_empty & empty_int;
	assign size = write_pointer - read_pointer;

	reg out_valid_pip_0;
	reg out_valid_pip_1;

	always @(posedge clk) begin
		if (in_valid && ~full)
			write_pointer <= write_pointer + 1'd1;

	 	if (out_req && ~empty) begin
			read_pointer <= read_pointer + 1'd1;
			out_valid_pip_0 <= out_req;
			out_valid_pip_1 <= out_valid_pip_0;
			out_valid <= out_valid_pip_1;
		end
	end

	xilinx_true_dual_port_read_first_2_clock_ram #(
		.RAM_WIDTH(WIDTH),
		.RAM_DEPTH(DEPTH),
		.RAM_PERFORMANCE("HIGH_PERFORMANCE")

		) buffer (

		// write port
		.clka(clk),
		.rsta(bram_rst),
		.ena(1'b1),
		.addra(write_pointer),
		.dina(in),
		.wea(in_valid),
		.regcea(1'b1),
		.douta(),

		// read port
		.clkb(clk),
		.rstb(bram_rst),
		.enb(1'b1),
		.addrb(read_pointer),
		.dinb(),
		.web(1'b0),
		.regceb(1'b1),
		.doutb(out));
	endmodule

`default_nettype wire
