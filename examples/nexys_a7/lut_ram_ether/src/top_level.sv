`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
    input wire btnc,
    input wire btnd,

    input wire [15:0] sw,

    output reg eth_refclk,
    output reg eth_rstn,

    input wire eth_crsdv,
    input wire [1:0] eth_rxd,

    output reg eth_txen,
    output reg [1:0] eth_txd,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    assign eth_rstn = ~btnc;

    logic clk_50mhz;
    assign eth_refclk = clk_50mhz;
    divider d (.clk(clk), .ethclk(clk_50mhz));

    manta manta_inst (
        .clk(clk_50mhz),

        .crsdv(eth_crsdv),
        .rxd(eth_rxd),
        .txen(eth_txen),
        .txd(eth_txd));


endmodule

`default_nettype wire