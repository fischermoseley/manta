`default_nettype none
`timescale 1ns / 1ps

`include "manta.v"

module top_level (
	input wire clk,

	input wire rs232_rx_ttl,
	output logic rs232_tx_ttl
	);

    manta manta_inst (
        .clk(clk),

        .rx(rs232_rx_ttl),
        .tx(rs232_tx_ttl));
endmodule

`default_nettype wire