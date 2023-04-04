`default_nettype none
`timescale 1ns / 1ps

`include "manta.v"

module top_level (
	input wire clk,

    output logic LED0,
    output logic LED1,
    output logic LED2,
    output logic LED3,
    output logic LED4,

	input wire rs232_rx_ttl,
	output logic rs232_tx_ttl
	);

    manta manta_inst (
        .clk(clk),

        .rx(rs232_rx_ttl),
        .tx(rs232_tx_ttl),

        .LED0(LED0),
        .LED1(LED1),
        .LED2(LED2),
        .LED3(LED3),
        .LED4(LED4));
endmodule

`default_nettype wire