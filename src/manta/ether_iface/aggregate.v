`default_nettype none
`timescale 1ns / 1ps

/* Aggregates the first 64 bits of an incoming
 * Ethernet transmission (thus shedding the FCS
 * and anything else extraneous) and outputs the
 * first 32 bits on an AXI bus for a single cycle.
 * If the packet is not at least 64 bits long,
 * nothing happens
 */

`define AGR_MAX		56
`define AGR_SHOW	64

module aggregate (
	input wire clk,
	input wire [1:0] axiid,
	input wire axiiv,

	output reg [55:0] axiod,
	output reg axiov);

	/* A quick and dirty counter. As long as this is below
	 * 32, we'll dump packets into the AXI output data buffer.
	 * Once the counter gets to AGR_MAX, we'll assert AXI valid.
	 * Then we'll hang until axiiv drops
	 */

	reg [31:0] counter;

	assign axiov = counter == `AGR_SHOW;

	always @(posedge clk) begin: COUNTER
		if (!axiiv) counter <= 32'b0;
		else counter <= counter + 2;
	end

	always @(posedge clk) begin: AXIOD
		if (!axiiv) axiod <= 32'b0;
		else if (counter < `AGR_MAX && axiiv)
			axiod[`AGR_MAX - counter - 2 +: 2] <= axiid;
	end

endmodule

`default_nettype wire
