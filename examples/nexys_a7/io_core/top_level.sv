`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
    input wire cpu_resetn,

    input wire btnu,
    input wire btnd,
    input wire btnl,
    input wire btnr,
	input wire btnc,

    input wire [15:0] sw,

	output logic [15:0] led,
    output logic led16_b,
    output logic led16_g,
    output logic led16_r,
    output logic led17_b,
    output logic led17_g,
    output logic led17_r,


    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic [7:0] an,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    manta manta (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out),

        .btnu(btnu),
        .btnd(btnd),
        .btnl(btnl),
        .btnr(btnr),
        .btnc(btnc),
        .sw(sw),
        .led(led),
        .led16_b(led16_b),
        .led16_g(led16_g),
        .led16_r(led16_r),
        .led17_b(led17_b),
        .led17_g(led17_g),
        .led17_r(led17_r));

    ssd ssd (
        .clk(clk),
        .val( (manta.my_io_core_btx_rdata << 16) | (manta.brx_my_io_core_wdata) ),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));

endmodule

`default_nettype wire