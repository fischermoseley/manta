`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    output logic [15:0] led,
    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic dp,
    output logic [7:0] an,

    output logic led16_r,
    output logic led17_r,

    output reg eth_refclk,
    output reg eth_rstn,

    input wire eth_crsdv,
    input wire [1:0] eth_rxd,

    output reg eth_txen,
    output reg [1:0] eth_txd);

    assign eth_rstn = 1;

    logic clk_50mhz;
    assign eth_refclk = clk_50mhz;
    divider d (.clk(clk), .ethclk(clk_50mhz));

    manta manta_inst (
        .clk(clk_50mhz),

        .crsdv(eth_crsdv),
        .rxd(eth_rxd),
        .txen(eth_txen),
        .txd(eth_txd));

    // Show bus on 7-segment display
    reg [15:0] addr_latched = 0;
    reg [15:0] data_latched = 0;
    reg rw_latched = 0;

    always @(posedge clk) begin
        if (manta.brx_my_lut_mem_valid) begin
            addr_latched <= manta.my_lut_mem_brx_addr;
            data_latched <= manta.my_lut_mem_brx_data;
            rw_latched <= manta.my_lut_mem_btx_rw;
        end
    end

    ssd ssd (
        .clk(clk),
        .val( (addr_latched << 16) | (data_latched) ),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));

    assign dp = rw_latched;
endmodule

`default_nettype wire