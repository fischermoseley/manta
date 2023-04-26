`default_nettype none
`timescale 1ns / 1ps

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

module ether (
	input wire clk,
	input wire [1:0] rxd,
	input wire crsdv,

	output reg axiov,
	output reg [1:0] axiod);

	reg [4:0] count;
	reg [2:0] state;

	reg [1:0] preamex;
	reg preamok, start;

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

	initial begin
		axiod = 2'b0;
		axiov = 1'b0;
		state = 3'b0;
	end

	always @(posedge clk) begin: FSM
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
endmodule

`default_nettype wire
