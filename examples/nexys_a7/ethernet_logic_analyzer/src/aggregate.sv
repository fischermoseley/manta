`default_nettype none
`timescale 1ns / 1ps

/* Aggregates the first 64 bits of an incoming
 * Ethernet transmission (thus shedding the FCS
 * and anything else extraneous) and outputs the
 * first 32 bits on an AXI bus for a single cycle.
 * If the packet is not at least 64 bits long,
 * nothing happens
 *
 * This value can then be fed into the seven
 * segment display to verify proper operation
 * of your module!
 */

`define AGR_MAX		32
`define AGR_SHOW	64

module aggregate(clk, rst, axiid, axiiv, axiod, axiov);

	/* batteries */
	input logic clk, rst;

	/* AXI input valid, and AXI input data from the
	 * Ethernet pipeline. Comprises only data, i.e.
	 * source/destination/ethertype are omitted via
	 * previous stages in the pipeline. Also technically
	 * comprises the FCS, but we assume that the actual
	 * data in the ethernet frame is >= 32 bits long
	 * so we'll lose the FCS in this stage by design
	 */
	input logic[1:0] axiid;
	input logic axiiv;

	/* AXI output valid, and AXI output data. Comprises
	 * just the first 32 bits of the incoming transmission,
	 * asserted for a single cycle
	 */
 	output logic[31:0] axiod;
	output logic axiov;
	
	/* A quick and dirty counter. As long as this is below
	 * 32, we'll dump packets into the AXI output data buffer.
	 * Once the counter gets to AGR_MAX, we'll assert AXI valid.
	 * Then we'll hang until axiiv drops
	 */
	logic[31:0] counter;

	assign axiov = counter == `AGR_SHOW;

	always_ff @(posedge clk) begin: COUNTER
		if (rst || !axiiv) counter <= 32'b0;
		else counter <= counter + 2;
	end

	always_ff @(posedge clk) begin: AXIOD
		if (rst || !axiiv) axiod <= 32'b0;
		else if (counter < `AGR_MAX && axiiv)
			axiod[`AGR_MAX - counter - 2 +: 2] = axiid;
	end

endmodule

`default_nettype wire
