`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
	input wire btnc,

	output logic [15:0] led,
    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic [7:0] an,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out));

    assign led = manta_inst.brx_my_lut_mem_addr;

    ssd ssd (
        .clk(clk),
        .val( {manta_inst.my_lut_mem_btx_rdata, manta_inst.brx_my_lut_mem_wdata} ),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));

endmodule

`default_nettype wire