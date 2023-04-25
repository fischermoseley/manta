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

    reg [15:0] data_buf = 0;
    always @(posedge clk) if(~rw_i && valid_i) data_buf <= rdata_i;

    mac_tx mtx (
        .clk(clk),

        .data(data_buf),
        .ethertype(16'h2),
        .start(~rw_i && valid_i),

        .txen(txen),
        .txd(txd));

endmodule

`default_nettype wire