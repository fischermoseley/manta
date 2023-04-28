`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

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

    // debugging!
    initial led17_r = 0;
    reg [31:0] val = 0;

    always @(posedge clk_50mhz) begin
        if(manta_inst.my_lut_mem.valid_o) begin
            led <= manta_inst.my_lut_mem.addr_o;
            led16_r <= manta_inst.my_lut_mem.rw_o;
            led17_r <= !led17_r;
            val <= {manta_inst.my_lut_mem.rdata_o, manta_inst.my_lut_mem.wdata_o};
        end
    end

    ssd ssd (
        .clk(clk_50mhz),
        .val(val),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));


endmodule

`default_nettype wire