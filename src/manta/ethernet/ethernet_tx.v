`default_nettype none
`timescale 1ns/1ps

module ethernet_tx (
    input wire clk,

    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i,

    output reg txen,
    output reg [1:0] txd
    );

    parameter FPGA_MAC = 0;
    parameter HOST_MAC = 0;
    parameter ETHERTYPE = 0;

    reg [15:0] rdata_buf = 0;

    always @(posedge clk)
        if(~rw_i && valid_i) rdata_buf <= rdata_i;

    mac_tx #(
        .SRC_MAC(FPGA_MAC),
        .DST_MAC(HOST_MAC),
        .ETHERTYPE(ETHERTYPE),
        .PAYLOAD_LENGTH_BYTES(2)
    ) mtx (
        .clk(clk),

        .payload(rdata_buf),
        .start(~rw_i && valid_i),

        .txen(txen),
        .txd(txd));

endmodule

`default_nettype wire