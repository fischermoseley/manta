`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    logic [4:0] counter = 0;
    always @(posedge clk) counter <= counter + 1;

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .spike(counter[0]),
        .jet(counter[1:0]),
        .valentine(counter[2:0]),
        .ed(counter[3:0]),
        .ein(counter));

endmodule

`default_nettype wire