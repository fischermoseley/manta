`default_nettype none
`timescale 1ns / 1ps

module top_level (
	input wire clk_100mhz,
    input wire [7:0] sw,
    output logic [7:0] led,

    input wire uart_tx_in,
	output logic uart_rx_out);

    manta manta_inst (
        .clk(clk_100mhz),
        .rst(0),

        .rx(uart_tx_in),
        .tx(uart_rx_out),

        .user_addr(sw),
        .user_data_out(led));

endmodule

`default_nettype wire