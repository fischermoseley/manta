`default_nettype none
`timescale 1ns / 1ps

`define LAGGING_SHIFT_IN (caxiod[30] ^ axiid[1])
`define LEADING_SHIFT_IN (caxiod[31] ^ axiid[0])
`define DOUBLED_SHIFT_IN (`LEADING_SHIFT_IN ^ `LAGGING_SHIFT_IN)

`define LAGGING_TAPS 4, 7, 10, 16, 22, 26
`define DOUBLED_TAPS 2, 5, 8, 11, 12, 23
`define LEADING_TAPS 3, 6, 9, 13, 17, 24, 27

/* this module implements CRC32-BZIP2, with a two bit input:
 *	- poly 0x04C11DB7
 *	- init 0xFFFFFFFF
 *	- NEW: XOR outputs
 *
 *	== check: 0xfc891918 ==
 *
 * this is the ethernet checksum!!
 */

module crc32(clk, rst, axiiv, axiid, axiov, axiod);

	/* old style i/o declaration, for clarity.
	 * easier on 80-char line limits...
	 * use this if you want, we don't care
	 */
	input logic clk, rst;

	input logic axiiv;
	input logic[1:0] axiid;

	output logic axiov;
	output logic[31:0] axiod;

	logic[31:0] caxiod, saxiod;
	integer i;

	assign axiov = 1;
	assign axiod = ~caxiod;

	always @(*) begin
		for (i = 0; i < 32; i = i + 1) begin
			case (i)
			0: saxiod[i] = `LAGGING_SHIFT_IN;
			1: saxiod[i] = `DOUBLED_SHIFT_IN;

			`LAGGING_TAPS:
				saxiod[i] = caxiod[i - 2] ^ `LAGGING_SHIFT_IN;
			`DOUBLED_TAPS:
				saxiod[i] = caxiod[i - 2] ^ `DOUBLED_SHIFT_IN;
			`LEADING_TAPS:
				saxiod[i] = caxiod[i - 2] ^ `LEADING_SHIFT_IN;

			default: saxiod[i] = caxiod[i - 2];
			endcase
		end
	end

	always @(posedge clk) begin
		if (rst) caxiod <= 32'hFFFF_FFFF;

		/* our output validity hinges on whether
		 * we are calculating anything or not
		 * on this clock cycle. if there is no
		 * valid input for us, don't do a shift
	 	 * this cycle
		 */
		else caxiod <= (axiiv) ? saxiod : caxiod;
	end

endmodule

`default_nettype wire
