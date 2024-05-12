`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
    input wire [15:0] sw,
    output logic [15:0] led,

    input wire uart_txd_in,
	output logic uart_rxd_out);

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .user_addr(sw),
        .user_data_out(led));

endmodule

`default_nettype wire