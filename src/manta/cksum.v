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

module cksum(clk, rst, axiid, axiiv, done, kill);

	/* batteries */
	input logic clk, rst;

	/* AXI input valid, and AXI input data from the
	 * physical layer. Comprises unmodified data directly
	 * from the wire, in Ethernet bit order, to be fed
	 * directly into the CRC32 module you wrote for the
	 * pset
	 */
	input logic[1:0] axiid;
	input logic axiiv;

	/* Done and kill, as described in the module synopsis */
	output logic done, kill;

	/* CRC32 AXI output data bus, which is the 32-bit
	 * checksum calculated so far via the checksum module
	 * you implemented in one of the last psets (CRC32-BZIP2)
	 */
	logic[31:0] crcd;
	logic crcv;

	/* Decoupled logic to reset the CRC module independently
	 * Used to compute multiple CRCs back to back
	 */
	logic crcrst;

	/* Our finite state machine - bonus points if you can identify
	 * whether this is a Moore or Mealy FSM!
	 */
	logic[1:0] state;

	crc32 cksum(.clk(clk),
		    .rst(crcrst | rst),
		    .axiiv(axiiv),
		    .axiid(axiid),
		    .axiov(crcv),
		    .axiod(crcd));

	always_ff @(posedge clk) begin: OUTPUTS
		if (rst || axiiv) begin
			done <= 1'b0;
			kill <= 1'b0;
			crcrst <= 1'b0;
		end else begin
			if (state == `CK_COMPUTING && !axiiv) begin
				done <= 1'b1;
				crcrst <= 1'b1;

				if (crcd == `MAGIC_CHECK) kill <= 1'b0;
				else kill <= 1'b1;
			end else crcrst <= 1'b0;
		end
	end

	always_ff @(posedge clk) begin: FSM
		if (rst) state <= `CK_FRESH;
		else begin
			case (state)
			`CK_FRESH: if (axiiv) state <= `CK_COMPUTING;
			`CK_COMPUTING: if (!axiiv) state <= `CK_DONE;
			`CK_DONE: if (axiiv) state <= `CK_COMPUTING;
			endcase
		end
	end

endmodule

`default_nettype wire
