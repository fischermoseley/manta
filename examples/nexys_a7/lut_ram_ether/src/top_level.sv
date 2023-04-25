`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
    input wire btnc,
    input wire btnd,

    input wire [15:0] sw,

    output logic [15:0] led,
    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic [7:0] an,

    output logic led16_r,
    output logic led17_r,

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

    assign led = manta_inst.brx_my_lut_ram_addr;
    assign led16_r = manta_inst.brx_my_lut_ram_rw;
    assign led17_r = manta_inst.brx_my_lut_ram_valid;

    logic [6:0] cat;
	assign {cg,cf,ce,cd,cc,cb,ca} = cat;
    ssd ssd (
        .clk_in(clk_50mhz),
        .rst_in(btnc),
        .val_in( {manta_inst.my_lut_ram_btx_rdata, manta_inst.brx_my_lut_ram_wdata} ),
        .cat_out(cat),
        .an_out(an));

    manta manta_inst (
        .clk(clk_50mhz),

        .crsdv(eth_crsdv),
        .rxd(eth_rxd),
        .txen(eth_txen),
        .txd(eth_txd));


endmodule

`default_nettype wire