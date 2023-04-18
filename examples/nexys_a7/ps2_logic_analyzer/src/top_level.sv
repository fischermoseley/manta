`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,

    input wire ps2_clk,
    input wire ps2_data,

    output logic [15:0] led,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    logic clk_50mhz;
    divider d (.clk(clk), .ethclk(clk_50mhz));

    assign led = manta_inst.my_logic_analyzer.la_controller.write_pointer;

    manta manta_inst (
        .clk(clk_50mhz),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .ps2_clk(ps2_clk),
        .ps2_data(ps2_data));

endmodule

`default_nettype wire