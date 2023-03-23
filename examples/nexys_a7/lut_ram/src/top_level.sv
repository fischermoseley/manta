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

    assign led = manta_inst.brx_my_lut_ram_addr;

    logic [6:0] cat;
	assign {cg,cf,ce,cd,cc,cb,ca} = cat;
    ssd ssd (
        .clk_in(clk),
        .rst_in(btnc),
        .val_in( (manta_inst.my_lut_ram_btx_rdata << 16) | (manta_inst.brx_my_lut_ram_wdata) ),
        .cat_out(cat),
        .an_out(an));

endmodule

`default_nettype wire