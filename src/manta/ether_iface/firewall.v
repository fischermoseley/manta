`default_nettype none
`timescale 1ns / 1ps

`define FW_DESTSTART	0
`define FW_DESTEND	(`FW_DESTSTART + 48)

`define FW_DATASTART	(48 + 48)

module firewall (
	input wire clk,
	input wire axiiv,
	input wire [1:0] axiid,

	output reg axiov,
	output reg [1:0] axiod);

	parameter ETHERTYPE = 0;
	parameter FPGA_MAC = 0;

	/* Buffers to hold our MAC address in the reverse order,
	 * to make comparison easier than it otherwise would be
	 */
	reg [0:47] me;

	/* A counter, to determine whether we should be comparing
	 * with a MAC address or stripping off data
	 */
	reg [31:0] counter;

	/* An internal set of flags to mark whether the currently
	 * traversing packet is valid, i.e we should forward data,
	 * or not. One of these flags tracks whether the destination
	 * MAC address matches _our_ (FW_ME) mac address, the other
	 * tracks whether the destination matches the broadcast
	 * (FW_BCAST) MAC. If either one of these is high once the
	 * destination MAC finishes rolling through, the packet
	 * is forwarded.
	 */
	reg matchme, matchbcast;

	assign me = FPGA_MAC;

	always @(posedge clk) begin: MATCH
		if (counter == 32'b0) begin
			matchme <= 1'b1;
			matchbcast <= 1'b1;
		end

		/* could overwrite the above, which is ideal if
		 * FW_DESTSTART == 0 (it is) and we have a mismatch
		 * out the gate
		 */
		if (counter >= `FW_DESTSTART && counter < `FW_DESTEND) begin
			if (axiiv) begin
				if (axiid != {me[counter], me[counter + 1]})
					matchme <= 1'b0;
				if (axiid != 2'b11)
					matchbcast <= 1'b0;
			end
		end
	end

	always @(*) begin: AXIOUT
		if (counter >= `FW_DATASTART && (matchme | matchbcast)) begin
			axiod = axiid;
			axiov = axiiv;
		end else begin
			axiod = 2'b00;
			axiov = 1'b0;
		end
	end

	always @(posedge clk) begin: COUNTER
		if (axiiv) counter <= counter + 2;
		else counter <= 32'b0;
	end

endmodule

`default_nettype wire
