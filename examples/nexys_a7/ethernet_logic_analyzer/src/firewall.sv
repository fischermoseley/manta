`default_nettype none
`timescale 1ns / 1ps

/* Sometimes we might receive packets not
 * intended for us on the wire. This is especially
 * true if we're operating in old school mode, where
 * Ethernet used to have many devices on the same
 * medium. Alternatively, several virtual NICs may
 * exist in software on a given machine, or a machine
 * may support MAC address randomization.
 *
 * All of this means we need to make sure inbound
 * packets are actually intended for us, and not
 * for some other NIC. That's what this module is
 * for. In addition, this module will also strip
 * the MAC address pair (and Ethertype) off of the
 * Ethernet header, leaving only data and the FCS.
 * We'll clean up the FCS later...
 */

/* "Intended for us" means the following:
 * - has the destination MAC "`FW_ME" as defined below. Make this
 *	your own MAC of your choice - get creative!
 * - has the destination MAC of all 1s, i.e. a 'broadcast' packet
 *
 * If these conditions are not met on a given input stream, data
 * from the packet is dropped / not forwarded on through the
 * pipeline
 */

`define FW_ME		48'h69_69_5A_06_54_91
`define FW_DESTSTART	0
`define FW_DESTEND	(`FW_DESTSTART + 48)

`define FW_DATASTART	(48 + 48 + 16)

module firewall(clk, rst, axiiv, axiid, axiov, axiod);

	/* batteries */
	input logic clk, rst;

	/* AXI input valid, and AXI input data from the bit order
	 * flip module. So this will transport MSb/MSB first data
	 * coming off the wire - allowing you to compare with src/dst
	 * MAC addresses a bit more easily
	 */
	input logic[1:0] axiid;
	input logic axiiv;

	/* AXI output valid, and AXI output data. If and only if
	 * the packet is intended for our device as described above,
	 * this line will stream out the _data_ and _fcs_ (NOT the MAC
	 * addresses in the header, nor the ethertype - we're ignoring
	 * the latter this time around) we're receiving off the wire.
	 * If a kill-worthy condition is detected, these lines are
	 * deasserted for the duration of the incoming packet
	 */
	output logic[1:0] axiod;
	output logic axiov;

	/* Buffers to hold our MAC address in the reverse order,
	 * to make comparison easier than it otherwise would be
	 */
	logic[0:47] me;

	/* A counter, to determine whether we should be comparing
	 * with a MAC address or stripping off data
	 */
	logic[31:0] counter;

	/* An internal set of flags to mark whether the currently
	 * traversing packet is valid, i.e we should forward data,
	 * or not. One of these flags tracks whether the destination
	 * MAC address matches _our_ (FW_ME) mac address, the other
	 * tracks whether the destination matches the broadcast
	 * (FW_BCAST) MAC. If either one of these is high once the
	 * destination MAC finishes rolling through, the packet
	 * is forwarded.
	 */
	logic matchme, matchbcast;

	assign me = `FW_ME;

	always_ff @(posedge clk) begin: MATCH
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

	always_comb begin: AXIOUT
		if (counter >= `FW_DATASTART && (matchme | matchbcast)) begin
			axiod = axiid;
			axiov = axiiv;
		end else begin
			axiod = 2'b00;
			axiov = 1'b0;
		end
	end

	always_ff @(posedge clk) begin: COUNTER
		if (axiiv) counter <= counter + 2;
		else counter <= 32'b0;
	end

endmodule

`default_nettype wire
