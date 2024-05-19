`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk_100mhz,

    input wire uart_tx_in,
	output logic uart_rx_out,

    input wire btnu,
    input wire btnd,
    input wire btnl,
    input wire btnr,
	input wire btnc,
    input wire cpu_resetn,

    input wire [7:0] sw,

	output logic [7:0] led);

    manta manta_inst (
        .clk(clk_100mhz),
        .rst(0),

        .rx(uart_tx_in),
        .tx(uart_rx_out),

        .btnu(btnu),
        .btnd(btnd),
        .btnl(btnl),
        .btnr(btnr),
        .btnc(btnc),
        .cpu_resetn(cpu_resetn),
        .sw(sw),
        .led(led));

endmodule

`default_nettype wire