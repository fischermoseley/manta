`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    logic larry = 0;
    logic curly = 0;
    logic moe = 0;
    logic [3:0] shemp = 0;

    always_ff @(posedge clk) begin
        {larry, curly, moe, shemp} <= {larry, curly, moe, shemp} + 1;
    end

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp));

endmodule

`default_nettype wire