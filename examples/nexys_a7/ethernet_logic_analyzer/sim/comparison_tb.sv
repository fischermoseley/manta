`default_nettype none
`timescale 1ns/1ps

module comparison_tb();
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
    logic eth_crsdv_playback;
    logic [1:0] eth_rxd_playback;

    logic eth_crsdv_pb9k;
    logic [1:0] eth_rxd_pb9k;

    logic eth_crsdv_mtx;
    logic [1:0] eth_rxd_mtx;

    logic eth_crsdv_debug;
    logic [1:0] eth_rxd_debug;

    // assign eth_crsdv_debug = eth_crsdv_playback;
    // assign eth_rxd_debug = eth_rxd_playback;

    // assign eth_crsdv_debug = eth_crsdv_pb9k;
    // assign eth_rxd_debug = eth_rxd_pb9k;

    assign eth_crsdv_debug = eth_crsdv_mtx;
    assign eth_rxd_debug = eth_rxd_mtx;

    ether_la_playback #(.MEM_FILE("capture.mem")) ether_la_playback_inst (
        .clk(ethclk),
        .enable(enable),
        .done(),

        .eth_crsdv(eth_crsdv_playback),
        .eth_rxd(eth_rxd_playback),
        .eth_txen(),
        .eth_txd());

    logic pb9k_start;
    packet_blaster_9k pb9k (
        .clk(ethclk),
        .rst(rst),

        //.src_mac(48'h69_2C_08_30_75_FD),
        .src_mac(48'h00_00_00_00_00_00),
        .dst_mac(48'hFF_FF_FF_FF_FF_FF),

        .data(16'h5678),

        .start(pb9k_start),

        .txen(eth_crsdv_pb9k),
        .txd(eth_rxd_pb9k));

    logic mtx_start;
    mac_tx mtx (
        .clk(ethclk),

        .data(16'h5678),

        .start(mtx_start),

        .txen(eth_crsdv_mtx),
        .txd(eth_rxd_mtx));



	ether e(
        .clk(ethclk),
		.rst(rst),
		.rxd(eth_rxd_debug),
		.crsdv(eth_crsdv_debug),
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
        $dumpfile("comparison_tb.vcd");
        $dumpvars(0, comparison_tb);
        rst = 0;
        pb9k_start = 0;
        mtx_start = 0;
        #10;
        rst = 1;
        #10;
        rst = 0;
        #10;
        enable = 1;
        #430;
        pb9k_start = 1;
        #10;
        pb9k_start = 0;
        #60;
        mtx_start = 1 ;
        #10;
        mtx_start = 0;

        #5000;

        $finish();
    end

endmodule
`default_nettype wire