`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    input wire uart_txd_in,
	output logic uart_rxd_out);

    logic probe0;
    logic [1:0] probe1;
    logic [7:0] probe2;
    logic [19:0] probe3;

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .probe0(probe0),
        .probe1(probe1),
        .probe2(probe2),
        .probe3(probe3),
        .probe4(probe0),
        .probe5(probe1),
        .probe6(probe2),
        .probe7(probe3));

endmodule

`default_nettype wire