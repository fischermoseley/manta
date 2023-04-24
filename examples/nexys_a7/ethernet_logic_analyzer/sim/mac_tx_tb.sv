`default_nettype none
`timescale 1ns/1ps

module mac_tx_tb();
    logic ethclk;
    logic rst;

    always begin
        #5;
        ethclk = !ethclk;
    end

    /* batteries... */
	logic eth_crsdv;
	logic[1:0] eth_rxd;

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

	/* and here's the pipeline... */

    logic eth_crsdv_mtx;
    logic [1:0] eth_rxd_mtx;

    logic mtx_start;
    mac_tx mtx (
        .clk(ethclk),

        .data(16'h5679),

        .start(mtx_start),

        .txen(eth_crsdv_mtx),
        .txd(eth_rxd_mtx));

	ether e(
        .clk(ethclk),
		.rst(rst),
		.rxd(eth_rxd_mtx),
		.crsdv(eth_crsdv_mtx),
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

    initial begin
        ethclk = 0;
        $dumpfile("mac_tx_tb.vcd");
        $dumpvars(0, mac_tx_tb);
        rst = 0;
        mtx_start = 0;
        #10;
        rst = 1;
        #10;
        rst = 0;
        #10;
        mtx_start = 1;

        #10000;

        $finish();
    end

endmodule
`default_nettype wire