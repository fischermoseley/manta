`default_nettype none
`timescale 1ns / 1ps

`include "src/debug.sv"

module top_level (
	input wire clk,

	input wire rs232_rx_ttl,
	output logic rs232_tx_ttl
	);
    
    wire rst = 0;
	
    // Signal Generator
    logic [7:0] count;
    always_ff @(posedge clk) count <= count + 1;

    // debugger
    manta manta(
        .clk(clk),
        .rst(rst),
        .larry(count[0]),
        .curly(count[1]),
        .moe(count[2]),
        .shemp(count[3:0]),
        
        .rxd(rs232_rx_ttl),
        .txd(rs232_tx_ttl));

endmodule

`default_nettype wire