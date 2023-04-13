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

  logic clk_65mhz;

  clk_wiz_lab3 clk_gen(
    .clk_in1(clk_100mhz),
    .clk_out1(clk_65mhz));

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

  localparam WIDTH = 256;
  localparam HEIGHT = 256;

  // calculate rom address
  logic [$clog2(WIDTH*HEIGHT)-1:0] image_addr;
  assign image_addr = (hcount_in - x_in) + ((vcount_in - y_in) * WIDTH);

  logic in_sprite;
  assign in_sprite = ((hcount_in >= x_in && hcount_in < (x_in + WIDTH)) &&
                      (vcount_in >= y_in && vcount_in < (y_in + HEIGHT)));

  // image BRAM
  xilinx_single_port_ram_read_first #(
    .RAM_WIDTH(8),
    .RAM_DEPTH(WIDTH*HEIGHT),
    .RAM_PERFORMANCE("HIGH_PERFORMANCE"),
    .INIT_FILE(`FPATH(image.mem))
  ) image_bram (
    .addra(image_addr),
    .dina(),
    .clka(clk_65mhz),
    .wea(1'b0),
    .ena(1'b1),
    .rsta(1'b0),
    .regcea(1'b1),
    .douta(color_lookup));

  // lookup
  logic [7:0] color_lookup;

  // pallete BRAM
  xilinx_single_port_ram_read_first #(
    .RAM_WIDTH(12),
    .RAM_DEPTH(256),
    .RAM_PERFORMANCE("HIGH_PERFORMANCE"),
    .INIT_FILE(`FPATH(palette.mem))
  ) pallete_bram (
    .addra(color_lookup),
    .dina(),
    .clka(clk_65mhz),
    .wea(1'b0),
    .ena(1'b1),
    .rsta(1'b0),
    .regcea(1'b1),
    .douta(color));

  logic [11:0] color;

  // the following lines are required for the Nexys4 VGA circuit - do not change
  assign vga_r = ~blank ? color[11:8]: 0;
  assign vga_g = ~blank ? color[7:4] : 0;
  assign vga_b = ~blank ? color[3:0] : 0;

  assign vga_hs = ~hsync;
  assign vga_vs = ~vsync;
endmodule

`default_nettype wire
