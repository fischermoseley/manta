`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    input wire eth_crsdv,
    input wire [1:0] eth_rxd,
	output logic [1:0] eth_txd,
	output logic eth_txen,
    output logic eth_refclk,
    output logic eth_rstn,

    input wire btnu,
    input wire btnd,
    input wire btnl,
    input wire btnr,
	input wire btnc,
    input wire [15:0] sw,
	output logic [15:0] led,
    output logic led16_b,
    output logic led16_g,
    output logic led16_r,
    output logic led17_b,
    output logic led17_g,
    output logic led17_r);

	// 50MHz clock generation for the RMII
	logic ethclk;
	divider div (
		.clk(clk),
		.ethclk(ethclk));

	assign eth_rstn = 1;
	assign eth_refclk = ethclk;

	manta manta_inst (
		.clk(ethclk),

		.crsdv(eth_crsdv),
		.rxd(eth_rxd),
		.txen(eth_txen),
		.txd(eth_txd),

		.btnu(btnu),
		.btnd(btnd),
		.btnl(btnl),
		.btnr(btnr),
		.btnc(btnc),
		.sw(sw),
		.led(led),
		.led16_b(led16_b),
		.led16_g(led16_g),
		.led16_r(led16_r),
		.led17_b(led17_b),
		.led17_g(led17_g),
		.led17_r(led17_r));

endmodule

`default_nettype wire