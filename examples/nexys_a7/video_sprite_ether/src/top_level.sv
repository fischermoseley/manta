`timescale 1ns / 1ps
`default_nettype none

module top_level (
    input wire clk_100mhz,

    output reg eth_refclk,
    output reg eth_rstn,

    input wire eth_crsdv,
    input wire [1:0] eth_rxd,

    output reg eth_txen,
    output reg [1:0] eth_txd,

    output logic [3:0] vga_r, vga_g, vga_b,
    output logic vga_hs, vga_vs);

    assign eth_rstn = 1;

    // Clock generation
    logic clk_50mhz;
    logic clk_65mhz;
    assign eth_refclk = clk_50mhz;

    clk_gen gen(
        .clk_100mhz(clk_100mhz),
        .clk_50mhz(clk_50mhz),
        .clk_65mhz(clk_65mhz));

    // VGA signals
    logic [10:0] hcount;
    logic [9:0] vcount;
    logic hsync, vsync, blank;

    vga vga_gen(
        .pixel_clk_in(clk_65mhz),
        .hcount_out(hcount),
        .vcount_out(vcount),
        .hsync_out(hsync),
        .vsync_out(vsync),
        .blank_out(blank));

    // VGA Pipelining
    reg[1:0][10:0] hcount_pipe;
    reg[1:0][10:0] vcount_pipe;
    reg[1:0] hsync_pipe;
    reg[1:0] vsync_pipe;
    reg[1:0] blank_pipe;

    always_ff @(posedge clk_65mhz)begin
        hcount_pipe[0] <= hcount;
        vcount_pipe[0] <= vcount;
        hsync_pipe[0] <= hsync;
        vsync_pipe[0] <= vsync;
        blank_pipe[0] <= blank;
        for (int i=1; i<2; i = i+1)begin
            hcount_pipe[i] <= hcount_pipe[i-1];
            vcount_pipe[i] <= vcount_pipe[i-1];
            hsync_pipe[i] <= hsync_pipe[i-1];
            vsync_pipe[i] <= vsync_pipe[i-1];
            blank_pipe[i] <= blank_pipe[i-1];
        end
    end

    localparam WIDTH = 128;
    localparam HEIGHT = 128;

    localparam X = 0;
    localparam Y = 0;

    // calculate rom address
    logic [$clog2(WIDTH*HEIGHT)-1:0] image_addr;
    assign image_addr = (hcount - X) + ((vcount - Y) * WIDTH);

    logic in_sprite;
    assign in_sprite = ((hcount_pipe[1] >= X && hcount_pipe[1] < (X + WIDTH)) &&
                        (vcount_pipe[1] >= Y && vcount_pipe[1] < (Y + HEIGHT)));

    manta manta_inst (
        .clk(clk_50mhz),

        .crsdv(eth_crsdv),
        .rxd(eth_rxd),
        .txen(eth_txen),
        .txd(eth_txd),

        .image_mem_clk(clk_65mhz),
        .image_mem_addr(image_addr),
        .image_mem_din(),
        .image_mem_dout(sprite_color),
        .image_mem_we(1'b0));

    logic [11:0] sprite_color;
    logic [11:0] color;
    assign color = in_sprite ? sprite_color : 12'h0;

    // the following lines are required for the Nexys4 VGA circuit - do not change
    assign vga_r = ~blank_pipe[1] ? color[11:8]: 0;
    assign vga_g = ~blank_pipe[1] ? color[7:4] : 0;
    assign vga_b = ~blank_pipe[1] ? color[3:0] : 0;

    assign vga_hs = ~hsync_pipe[1];
    assign vga_vs = ~vsync_pipe[1];


endmodule
`default_nettype wire
