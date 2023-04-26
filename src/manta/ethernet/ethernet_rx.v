`default_nettype none
`timescale 1ns/1ps

module ethernet_rx (
    input wire clk,

    input wire crsdv,
    input wire [1:0] rxd,

    output reg [15:0] addr_o,
    output reg [15:0] wdata_o,
    output reg rw_o,
    output reg valid_o
    );

    parameter FPGA_MAC = 0;
    parameter ETHERTYPE = 0;

    reg [31:0] data;
    reg valid;

    mac_rx #(
        .DST_MAC(48'h69_69_5A_06_54_91),
        .ETHERTYPE(16'h88_B5)
    ) mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .payload(payload),
        .length(length)
        .valid(valid));

        assign addr_o = payload[31:16];
        assign wdata_o = payload[15:0];
        assign rw_o = (length == 4);
        assign valid_o = valid && ((length == 4) || (length == 2));

endmodule

`default_nettype wire