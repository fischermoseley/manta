`default_nettype none
`timescale 1ns/1ps
/*
This playback module was generated with Manta v0.0.0 on 24 Apr 2023 at 22:17:57 by fischerm

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

manta manta_inst (
    .clk(clk),

    .rx(rx),
    .tx(tx));

*/

module manta(
    input wire clk,

    input wire crsdv,
    input wire [1:0] rxd,

    output reg txen,
    output reg [1:0] txd);

    ethernet_rx erx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .addr_o(brx_my_lut_ram_addr),
        .wdata_o(brx_my_lut_ram_wdata),
        .rw_o(brx_my_lut_ram_rw),
        .valid_o(brx_my_lut_ram_valid));

    reg [15:0] brx_my_lut_ram_addr;
    reg [15:0] brx_my_lut_ram_wdata;
    reg brx_my_lut_ram_rw;
    reg brx_my_lut_ram_valid;


    lut_ram #(.DEPTH(64)) my_lut_ram (
        .clk(clk),

        .addr_i(brx_my_lut_ram_addr),
        .wdata_i(brx_my_lut_ram_wdata),
        .rdata_i(),
        .rw_i(brx_my_lut_ram_rw),
        .valid_i(brx_my_lut_ram_valid),

        .addr_o(),
        .wdata_o(),
        .rdata_o(my_lut_ram_btx_rdata),
        .rw_o(my_lut_ram_btx_rw),
        .valid_o(my_lut_ram_btx_valid));


    reg [15:0] my_lut_ram_btx_rdata;
    reg my_lut_ram_btx_rw;
    reg my_lut_ram_btx_valid;

    ethernet_tx etx (
        .clk(clk),

        .txen(txen),
        .txd(txd),

        .rdata_i(my_lut_ram_btx_rdata),
        .rw_i(my_lut_ram_btx_rw),
        .valid_i(my_lut_ram_btx_valid));

endmodule


module lut_ram (
    input wire clk,

    // input port
    input wire [15:0] addr_i,
    input wire [15:0] wdata_i,
    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i,

    // output port
    output reg [15:0] addr_o,
    output reg [15:0] wdata_o,
    output reg [15:0] rdata_o,
    output reg rw_o,
    output reg valid_o);

    parameter DEPTH = 8;
    parameter BASE_ADDR = 0;
    parameter READ_ONLY = 0;
    reg [DEPTH-1:0] mem [15:0];

    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;


        if(valid_i) begin
            // check if address is valid
            if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + DEPTH - 1) ) begin

                // read/write
                if (rw_i && !READ_ONLY) mem[addr_i - BASE_ADDR] <= wdata_i;
                else rdata_o <= mem[addr_i - BASE_ADDR];
            end
        end
    end
endmodule

`default_nettype wire