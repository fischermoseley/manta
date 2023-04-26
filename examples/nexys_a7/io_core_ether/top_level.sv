`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
    input wire cpu_resetn,

    input wire eth_crsdv,
    input wire [1:0] eth_rxd,
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
    output logic led17_r,


    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic [7:0] an,

	input wire uart_txd_in,
	output logic uart_rxd_out);

    logic rst;
    assign rst = ~cpu_resetn;

   /* the ethernet clock runs at 50mhz
	 * we run at 100mhz; divide the clock
	 * accordingly...
	 */
	logic ethclk;

	/* ether -> { cksum, bitorder } */
	logic[1:0] ether_axiod;
	logic ether_axiov;

	/* cksum -> top_level */
	logic cksum_done, cksum_kill;

	/* bitorder -> firewall */
	logic[1:0] bitorder_axiod;
	logic bitorder_axiov;

	/* firewall -> aggregate */
	logic[1:0] firewall_axiod;
	logic firewall_axiov;

	/* aggregate output */
	logic[31:0] aggregate_axiod;
	logic aggregate_axiov;

	divider div(
		.clk(clk),
		.ethclk(ethclk));

	ether e(
		.clk(ethclk),
		.rst(rst),
		.rxd(eth_rxd),
		.crsdv(eth_crsdv),
		.axiov(ether_axiov),
		.axiod(ether_axiod));

	bitorder b(
		.clk(ethclk),
		.rst(rst),
		.axiiv(ether_axiov),
		.axiid(ether_axiod),
		.axiov(bitorder_axiov),
		.axiod(bitorder_axiod));

	firewall f(
		.clk(ethclk),
		.rst(rst),
		.axiiv(bitorder_axiov),
		.axiid(bitorder_axiod),
		.axiov(firewall_axiov),
		.axiod(firewall_axiod));

	aggregate a(
		.clk(ethclk),
		.rst(rst),
		.axiiv(firewall_axiov),
		.axiid(firewall_axiod),
		.axiov(aggregate_axiov),
		.axiod(aggregate_axiod));

	cksum c(
		.clk(ethclk),
		.rst(rst),
		.axiiv(ether_axiov),
		.axiid(ether_axiod),
		.done(cksum_done),
		.kill(cksum_kill));

	assign eth_rstn = ~rst;
	assign eth_refclk = ethclk;

    manta manta (
        .clk(ethclk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .brx_my_io_core_addr(aggregate_axiod[31:16]),
        .brx_my_io_core_wdata(aggregate_axiod[15:0]),
        .brx_my_io_core_rw(1'b1),
        .brx_my_io_core_valid(aggregate_axiov),

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

    logic [31:0] aggregate_axiod_persistent;
    always_ff @(posedge ethclk) if (aggregate_axiov) aggregate_axiod_persistent <= aggregate_axiod;
    ssd ssd (
        .clk(ethclk),
        .val(aggregate_axiod_persistent),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));

endmodule

`default_nettype wire