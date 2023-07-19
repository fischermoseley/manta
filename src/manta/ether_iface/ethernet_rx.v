`default_nettype none
`timescale 1ns/1ps

module ethernet_rx (
    input wire clk,

    input wire crsdv,
    input wire [1:0] rxd,

    output reg [15:0] addr_o,
    output reg [15:0] data_o,
    output reg rw_o,
    output reg valid_o
    );

    parameter FPGA_MAC = 0;
    parameter ETHERTYPE = 0;

    reg [55:0] payload;
    reg valid;

    mac_rx #(
        .FPGA_MAC(FPGA_MAC),
        .ETHERTYPE(ETHERTYPE)
    ) mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .payload(payload),
        .valid(valid));

        assign rw_o = (payload[39:32] == 8'd1);
        assign addr_o = payload[31:16];
        assign data_o = payload[15:0];
        assign valid_o = valid && ( payload[39:32] == 8'd0 || payload[39:32] == 8'd1) && (payload[55:40] == 16'h88B5);

endmodule

`default_nettype wire