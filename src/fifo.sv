`default_nettype none
`timescale 1ns / 1ps

module fifo (
	input wire clk,
	input wire rst,

	input wire [WIDTH - 1:0] data_in,
	input wire input_ready,

	input wire request_output,
	output logic [WIDTH - 1:0] data_out,
	output logic output_valid,

	output logic [AW:0] size,
	output logic empty,
	output logic full
	);

	parameter WIDTH = 8;
	parameter DEPTH = 4096;
	localparam AW = $clog2(DEPTH);

	logic [AW:0] write_pointer;
	logic [AW:0] read_pointer;

	logic empty_int;
	assign empty_int = (write_pointer[AW] == read_pointer[AW]);

	logic full_or_empty;
	assign full_or_empty = (write_pointer[AW-1:0] ==	read_pointer[AW-1:0]);

	assign full = full_or_empty & !empty_int;
	assign empty = full_or_empty & empty_int;
	assign size = write_pointer - read_pointer;

	logic output_valid_pip_0;
	logic output_valid_pip_1;

	always @(posedge clk) begin
		if (input_ready && ~full)
			write_pointer <= write_pointer + 1'd1;

	 	if (request_output && ~empty)
			read_pointer <= read_pointer + 1'd1;
			output_valid_pip_0 <= request_output;
			output_valid_pip_1 <= output_valid_pip_0;
			output_valid <= output_valid_pip_1;

		if (rst) begin
			read_pointer  <= 0;
			write_pointer <= 0;
		end
	end

	xilinx_true_dual_port_read_first_2_clock_ram #(
		.RAM_WIDTH(WIDTH),
		.RAM_DEPTH(DEPTH),
		.RAM_PERFORMANCE("HIGH_PERFORMANCE")

		) buffer (

		// write port
		.clka(clk),
		.rsta(rst),
		.ena(1),
		.addra(write_pointer),
		.dina(data_in),
		.wea(input_ready),
		.regcea(1),
		.douta(),

		// read port
		.clkb(clk),
		.rstb(rst),
		.enb(1),
		.addrb(read_pointer),
		.dinb(),
		.web(0),
		.regceb(1),
		.doutb(data_out));
	endmodule

`default_nettype wire
