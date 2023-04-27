`default_nettype none
`timescale 1ns / 1ps

/* Computes the ethernet checksum
 * The following combinations of `done` and `kill`
 * represent the state of the module:
 *
 * - done = 0, kill = 0: processing data or freshly reset
 * - done = 1, kill = 0: correct ethernet checksum verified
 * - done = 1, kill = 1: data valid set to zero before correct
 *	checksum value computed, therefore bad checksum
 * - done = 0, kill = 1: never asserted
 *
 * the done and/or kill signals are asserted high beginning
 * the cycle after input data ceases, and until new data
 * is received via the AXI input
 */

`define CK_FRESH	2'b00
`define CK_COMPUTING	2'b01
`define CK_DONE		2'b10

`define MAGIC_CHECK	32'h38_fb_22_84

module cksum (
	input wire clk,
	input wire [1:0] axiid,
	input wire axiiv,

	output reg done,
	output reg kill);

	reg [31:0] crcd;
	reg crcv;

	/* Decoupled logic to reset the CRC module independently
	 * Used to compute multiple CRCs back to back
	 */
	reg crcrst;

	reg [1:0] state = `CK_FRESH;
	initial done = 0;
	initial kill = 0;
	initial crcrst = 0;

	crc32 cksum(
		.clk(clk),
		.rst(crcrst),
		.axiiv(axiiv),
		.axiid(axiid),
		.axiov(crcv),
		.axiod(crcd));

	always @(posedge clk) begin: OUTPUTS
		if (axiiv) begin
			done <= 1'b0;
			kill <= 1'b0;
			crcrst <= 1'b0;
		end else begin
			if (state == `CK_COMPUTING && !axiiv) begin
				done <= 1'b1;
				crcrst <= 1'b1;
                kill <= (crcd != `MAGIC_CHECK);
			end

            else crcrst <= 1'b0;
		end
	end

	always @(posedge clk) begin: FSM
		case (state)
			`CK_FRESH: if (axiiv) state <= `CK_COMPUTING;
			`CK_COMPUTING: if (!axiiv) state <= `CK_DONE;
			`CK_DONE: if (axiiv) state <= `CK_COMPUTING;
		endcase
	end

endmodule

`default_nettype wire
