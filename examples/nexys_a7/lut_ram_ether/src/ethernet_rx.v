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

    // we know if the packet is a read or write
    // based on the ethertype.

    reg [15:0] ethertype;
    reg [31:0] data;
    reg valid;

    mac_rx mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .ethertype(ethertype),
        .data(data),
        .valid(valid));

        assign addr_o = data[31:16];
        assign wdata_o = data[15:0];
        assign rw_o = (ethertype == 4);
        assign valid_o = valid && ((ethertype == 4) || (ethertype == 2));

endmodule

`default_nettype wire