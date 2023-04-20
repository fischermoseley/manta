`default_nettype none
`timescale 1ns/1ps

module packet_blaster_9k_tb();
    logic ethclk;
    logic rst;

    always begin
        #5;
        ethclk = !ethclk;
    end

    /* batteries... */
	logic eth_crsdv;
	logic[1:0] eth_rxd;

	logic eth_refclk;
	logic eth_rstn;

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

    logic enable;
    logic eth_crsdv_ref;
    logic [1:0] eth_rxd_ref;
    ether_la_playback #(.MEM_FILE("capture.mem")) ether_la_playback_inst (
        .clk(ethclk),
        .enable(enable),
        .done(),

        .eth_crsdv(eth_crsdv_ref),
        .eth_rxd(eth_rxd_ref),
        .eth_txen(),
        .eth_txd());

    logic start;
    packet_blaster_9k pb9k (
        .clk(ethclk),
        .rst(rst),

        //.src_mac(48'h69_2C_08_30_75_FD),
        .src_mac(48'h00_00_00_00_00_00),
        .dst_mac(48'hFF_FF_FF_FF_FF_FF),

        .data(16'h5678),

        .start(start),

        .txen(eth_crsdv),
        .txd(eth_rxd));

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

    initial begin
        ethclk = 0;
        $dumpfile("packet_blaster_9k_tb.vcd");
        $dumpvars(0, packet_blaster_9k_tb);
        rst = 0;
        start = 0;
        #10;
        rst = 1;
        #10;
        rst = 0;
        #10;
        enable = 1;
        #430;
        start = 1;
        #10;
        start = 0;

        #5000;

        $finish();
    end

endmodule
`default_nettype wire