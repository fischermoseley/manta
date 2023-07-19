`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
	input wire btnc,

	output logic [15:0] led,
    output logic ca, cb, cc, cd, ce, cf, cg,
    output logic dp,
    output logic [7:0] an,

	input wire uart_txd_in,
	output logic uart_rxd_out
	);

    manta manta_inst (
        .clk(clk),

        .rx(uart_txd_in),
        .tx(uart_rxd_out));

    // Show bus on 7-segment display
    reg [15:0] addr_latched = 0;
    reg [15:0] data_latched = 0;
    reg rw_latched = 0;

    always @(posedge clk) begin
        if (manta.brx_my_lut_mem_valid) begin
            addr_latched <= manta.my_lut_mem_brx_addr;
            data_latched <= manta.my_lut_mem_brx_data;
            rw_latched <= manta.my_lut_mem_btx_rw;
        end
    end

    ssd ssd (
        .clk(clk),
        .val( (addr_latched << 16) | (data_latched) ),
        .cat({cg,cf,ce,cd,cc,cb,ca}),
        .an(an));

    assign dp = rw_latched;

endmodule

`default_nettype wire