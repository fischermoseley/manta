`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
	input wire [7:0] ja,
	input wire [7:0] jb,
	input wire [1:0] jc,
	output logic [1:0] jd);

	dual_port_bram #(.RAM_DEPTH(256), .RAM_WIDTH(2)) bram_0 (
		.clka(clk),
		.addra(ja),
		.dina(jc),
		.douta(),
		.wea(1'b1),

		.clkb(clk),
		.addrb(jb),
		.dinb(8'b0),
		.doutb(jd),
		.web(1'b0)
	);

endmodule

`default_nettype wire