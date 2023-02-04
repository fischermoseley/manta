`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk,
	input wire btnc,
	input wire btnu,
	input wire [15:0] sw,

	output logic [15:0] led,
	input wire uart_txd_in,
	output logic uart_rxd_out
	);
	
    // Signal Generator
    logic [7:0] count;
    always_ff @(posedge clk) count <= count + 1;

    // ILA
    // later make this a #ILA that gets loaded from a svh file that the python script generates
    ila ila(
        .clk(clk),
        .rst(btnc),
        .larry(count[0]),
        .curly(count[1]),
        .moe(count[2]),
        .shemp(count[5:3]),
        
        .rxd(uart_txd_in),
        .txd(uart_rxd_out));

endmodule

`default_nettype wire