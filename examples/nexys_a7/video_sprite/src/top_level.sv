`timescale 1ns / 1ps
`default_nettype none

module top_level(
  input wire clk_100mhz,
  input wire [15:0] sw,
  input wire btnc, btnu, btnl, btnr, btnd,

  output logic [15:0] led,

  output logic [3:0] vga_r, vga_g, vga_b,
  output logic vga_hs, vga_vs
  );

  /* Video Pipeline */
  logic clk_65mhz;

  clk_wiz_lab3 clk_gen(
    .clk_in1(clk_100mhz),
    .clk_out1(clk_65mhz));

  logic [10:0] hcount;    // pixel on current line
  logic [9:0] vcount;     // line number
  logic hsync, vsync, blank; //control signals for vga

  vga vga_gen(
    .pixel_clk_in(clk_65mhz),
    .hcount_out(hcount),
    .vcount_out(vcount),
    .hsync_out(hsync),
    .vsync_out(vsync),
    .blank_out(blank));

  image_sprite img_sprite (
    .pixel_clk_in(clk_65mhz),
    .rst_in(btnc),
    .x_in(0),
    .hcount_in(hcount),
    .y_in(0),
    .vcount_in(vcount),
    .pixel_out(color));

  logic [11:0] color;

  // the following lines are required for the Nexys4 VGA circuit - do not change
  assign vga_r = ~blank ? color[11:8]: 0;
  assign vga_g = ~blank ? color[7:4] : 0;
  assign vga_b = ~blank ? color[3:0] : 0;

  assign vga_hs = ~hsync;
  assign vga_vs = ~vsync;
endmodule

`default_nettype wire
