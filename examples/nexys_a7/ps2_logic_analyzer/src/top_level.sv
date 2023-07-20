`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    input wire ps2_clk,
    input wire ps2_data,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .ps2_clk(ps2_clk),
        .ps2_data(ps2_data));

endmodule

`default_nettype wire