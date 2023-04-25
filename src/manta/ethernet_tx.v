`default_nettype none
`timescale 1ns/1ps

module ethernet_tx(
    input wire clk,

    output reg txen,
    output reg [1:0] txd,

    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i
    );

    mac_tx mtx (
        .clk(clk),

        .data(rdata_i),
        .ethertype(16'h2),
        .start(~rw_i && valid_i),

        .txen(txen),
        .txd(txd));

endmodule

`default_nettype wire