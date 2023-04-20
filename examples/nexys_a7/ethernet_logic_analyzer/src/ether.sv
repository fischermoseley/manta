/* The catsoop checker does not like to see `timescale declarations
 * in your code. However, we obviously need them when we synthesize
 * for iverilog - they tell iverilog that #5 means 5ns, for example.
 * Without these iverilog has no basis for how long *stuff* should
 * wait for when you use #, so it blows up!
 *
 * When you use the catsoop checker, it `defines the CATSOOP macro.
 * So we can check whether CATSOOP is defined or not - if it isn't,
 * then we'll put the timescale thing in so code works right on your
 * system.
 */

`default_nettype none
`timescale 1ns / 1ps

/* This module receives packets from the RJ45 (Ethernet) port on your
 * FPGA from the _physical layer_, i.e. the electronic (or optical!)
 * connection between devices running through an Ethernet cable.
 *
 * Ethernet is very diverse set of specifications, with all sorts of
 * different physical layers (which we abbreviate 'the medium' or
 * 'media' in plural). Ethernet media have transfer speeds ranging
 * from 1 Mbps to 400 gigabits per second in modern data centers!
 * For this implementation, we will implement "Fast Ethernet", which
 * (not fast by today's standards) utilizes a physical layer capable
 * of 100 Mbps communication. Most modern cables are backwards
 * compatible with this standard.
 */

/* Note: this file uses tabs instead of spaces for indentation.
 * More modern editors should pick this up automatically, but if yours
 * doesn't that might explain trouble getting things to line up. You
 * can probably configure this (e.g. in vim, type ":set noexpandtab"
 * in normal mode and then type ":set tabstop=8")
 */

`define EF_IDLE		3'b000
`define EF_PREAM	3'b001
`define EF_DATA		3'b011
`define EF_BAD		3'b101	

`define PREAM_BITS	64
`define PREAM_SIZE	(`PREAM_BITS / 2)

`define PREAM_FIRST	2'b00
`define PREAM_EXPECT	2'b01
`define PREAM_LAST	2'b11
`define PREAM_BAD	2'b10

module ether(clk, rst, rxd, crsdv, axiov, axiod);

	input logic clk, rst;

	/* Carrier Sense (CRS) / Data Valid (DV): indicates
	 * whether there is a valid signal currently being
	 * transmitted over the Ethernet medium by another
	 * sender.
	 *
	 * In the past, >2 computers were connected
	 * to the same Ethernet cable, so this helped
	 * distinguish if one machine was trying to talk over
	 * another. Nowadays, usually Ethernet connections are
 	 * point to point (have you ever seen an Ethernet cable
	 * with three ports on it? no? that's what i thought),
	 * and shared media isn't even supported in the 100 Mbps
	 * spec.
	 *
	 * So just use this input to determine whether valid
	 * data is on the line coming in.
	 */
	input logic crsdv;	

	/* Receive Data (RXD): If crsdv is high, receives
	 * two bits off the wire. Otherwise, undefined
	 * (let's say 2'bXX)
	 *
	 * According to the IEEE 802.3 Fast Ethernet
	 * specification, with the exception of the FCS,
	 * bytes in Ethernet world are sent least significant
	 * bit first, most significant byte first. Confusing!
	 * Basically, if you have a two byte (16 bit) message,
	 * the bits will come in over RXD as:
	 *
	 * 7:6 -> 5:4 -> 3:2 -> 1:0 -> 15:14 -> ... -> 9:8
	 *
	 * For now, this idiosyncracy won't matter to you.
	 * Later, it will.
	 */
	input logic[1:0] rxd;

	/* 2-bit AXI output: forward whatever we receive
	 * on to the outside world for further processing
	 */
	output logic axiov;
	output logic[1:0] axiod;

	/* END OF STARTER CODE */

	logic[4:0] count;
	logic[2:0] state;

	logic[1:0] preamex;
	logic preamok, start;

	always @(*) begin: PREAM
		if (count == `PREAM_SIZE - 1) preamex = `PREAM_LAST;
		else preamex = `PREAM_EXPECT;

		preamok = crsdv && rxd == preamex;
	end
	
	always @(*) start = crsdv && rxd != `PREAM_FIRST;

	always @(posedge clk) begin: COUNT
		if (state == `EF_PREAM) count <= count + 1;
		else if (state == `EF_IDLE && start) count <= count + 1;
		else count <= 0;
	end

	always @(posedge clk) begin: FSM
		if (rst) begin
			axiod <= 2'b0;
			axiov <= 1'b0;
			state <= 3'b0;
		end else begin
			case (state)
			`EF_BAD: if (!crsdv) state <= `EF_IDLE;
			`EF_IDLE: if (start) state <= `EF_PREAM;

			`EF_PREAM: begin
				if (!preamok || !crsdv) state <= `EF_BAD;
				else if (count == `PREAM_SIZE - 1)
					state <= `EF_DATA;
			end

			`EF_DATA: begin
				if (crsdv) begin
					axiov <= 1'b1;
					axiod <= rxd;
				end else begin
					axiov <= 1'b0;
					axiod <= 2'b0;
					state <= `EF_IDLE;
				end
			end
			endcase
		end
	end
endmodule

`default_nettype wire
