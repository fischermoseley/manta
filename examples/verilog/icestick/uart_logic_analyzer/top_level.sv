`default_nettype none
`timescale 1ns / 1ps

`include "manta.v"

module top_level (
	input wire clk,

	input wire rs232_rx_ttl,
	output logic rs232_tx_ttl
	);

    logic [9:0] counter;

    always @(posedge clk) counter <= counter + 1;

    assign probe0 = counter[0];
    assign probe1 = counter[2:1];
    assign probe2 = counter[5:3];
    assign probe4 = counter[9:6];

    manta manta_inst (
        .clk(clk),
        .rst(0),

        .rx(rs232_rx_ttl),
        .tx(rs232_tx_ttl),

        .probe0(probe0),
        .probe1(probe1),
        .probe2(probe2),
        .probe3(probe3));
endmodule

`default_nettype wire