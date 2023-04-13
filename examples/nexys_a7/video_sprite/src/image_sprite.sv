`timescale 1ns / 1ps
`default_nettype none

`include "iverilog_hack.svh"

module image_sprite #(
  parameter WIDTH=256, HEIGHT=256) (
  input wire pixel_clk_in,
  input wire rst_in,
  input wire [10:0] x_in, hcount_in,
  input wire [9:0]  y_in, vcount_in,
  output logic [11:0] pixel_out);

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
    .clka(pixel_clk_in),
    .wea(1'b0),
    .ena(1'b1),
    .rsta(1'b0),
    .regcea(1'b1),
    .douta(color_lookup)
    );

  // lookup
  logic [7:0] color_lookup;

  // pallete BRAM
  xilinx_single_port_ram_read_first #(
    .RAM_WIDTH(12),
    .RAM_DEPTH(256),
    .RAM_PERFORMANCE("HIGH_PERFORMANCE"),
    .INIT_FILE(`FPATH(pallete.mem))
  ) pallete_bram (
    .addra(color_lookup),
    .dina(),
    .clka(pixel_clk_in),
    .wea(1'b0),
    .ena(1'b1),
    .rsta(1'b0),
    .regcea(1'b1),
    .douta(color)
  );

  logic [11:0] color;

  assign pixel_out = in_sprite ? color : 0;
endmodule

`default_nettype none
