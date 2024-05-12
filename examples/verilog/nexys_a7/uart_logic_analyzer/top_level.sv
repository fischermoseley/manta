`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    logic probe0;
    logic [3:0] probe1;
    logic [7:0] probe2;
    logic [15:0] probe3;

    always @(posedge clk) begin
        probe0 <= probe0 + 1;
        probe1 <= probe1 + 1;
        probe2 <= probe2 + 1;
        probe3 <= probe3 + 1;
    end

    manta manta_inst (
        .clk(clk),
        .rst(0),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .probe0(probe0),
        .probe1(probe1),
        .probe2(probe2),
        .probe3(probe3));

endmodule

`default_nettype wire