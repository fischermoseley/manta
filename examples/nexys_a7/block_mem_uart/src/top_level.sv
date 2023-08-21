`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    input wire uart_txd_in,
	output logic uart_rxd_out);

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .my_block_memory_clk(clk),
        .my_block_memory_addr(0),
        .my_block_memory_din(0),
        .my_block_memory_dout(),
        .my_block_memory_we(0));

endmodule

`default_nettype wire