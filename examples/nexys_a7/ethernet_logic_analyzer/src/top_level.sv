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

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .eth_crsdv(eth_crsdv),
        .eth_rxd(eth_rxd),
        .eth_txen(eth_txen),
        .eth_txd(eth_txd));

    // packet_blaster_9k pb9k (
    //     .clk(clk_50mhz),
    //     .rst(btnc),

    //     //.src_mac(48'h69_2C_08_30_75_FD),
    //     .src_mac(48'b00_00_00_00_00_00),
    //     .dst_mac(48'hFF_FF_FF_FF_FF_FF),

    //     .data(16'h5678),

    //     .start(btnd),

    //     .txen(eth_txen),
    //     .txd(eth_txd));


    mac_tx mtx (
        .clk(clk_50mhz),

        .data(sw),

        .start(btnd),

        .txen(eth_txen),
        .txd(eth_txd));

endmodule

`default_nettype wire