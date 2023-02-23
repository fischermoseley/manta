`timescale 1ns / 1ps

module top_level(
    input wire clk,
    input wire sd_cd,
    input wire btnc,

    output logic [15:0] led,
    
    inout [3:0] sd_dat,
    output logic sd_reset,
    output logic sd_sck,
    output logic sd_cmd
    );

    assign sd_dat[2:1] = 2'b11;
    assign sd_reset = 0;

    // generate 25 mhz clock for sd_controller
    logic clk_25mhz;
    sd_clk_gen clk_gen(
        .clk_100mhz(clk), 
        .clk_25mhz(clk_25mhz));

    // sd_controller inputs
    logic rd;                   // read enable
    logic wr;                   // write enable
    logic [7:0] din;            // data to sd card
    logic [31:0] addr;          // starting address for read/write operation

    // sd_controller outputs
    logic ready;                // high when ready for new read/write operation
    logic [7:0] dout;           // data from sd card
    logic byte_available;       // high when byte available for read
    logic ready_for_next_byte;  // high when ready for new byte to be written

    // handles reading from the SD card
    sd_controller sd(
        .reset(btnc),
        .clk(clk_25mhz),
        .cs(sd_dat[3]),
        .mosi(sd_cmd),
        .miso(sd_dat[0]),
        .sclk(sd_sck),
        .ready(ready),
        .address(addr),
        .rd(rd),
        .dout(dout),
        .byte_available(byte_available),
        .wr(wr),
        .din(din),
        .ready_for_next_byte(ready_for_next_byte));

    // your Verilog here :)

endmodule