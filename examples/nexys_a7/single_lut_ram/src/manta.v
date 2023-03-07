`default_nettype none
`timescale 1ns/1ps

module manta(
    input wire clk,
    input wire rst,
    input wire rxd,
    output reg txd);

    rx_uart #(.CLOCKS_PER_BAUD(868)) urx (
        .i_clk(clk),
        .i_uart_rx(rxd),
        .o_wr(urx_brx_axiv),
        .o_data(urx_brx_axid));

    // uart_rx --> bridge_rx signals
    logic [7:0] urx_brx_axid;
    logic urx_brx_axiv;

    bridge_rx brx (
        .clk(clk),

        .axiid(urx_brx_axid),
        .axiiv(urx_brx_axiv),

        .req_addr(brx_mem_addr),
        .req_data(brx_mem_wdata),
        .req_rw(brx_mem_rw),
        .req_valid(brx_mem_valid),
        .req_ready(1'b1));

    // bridge_rx --> mem signals
    logic [15:0] brx_mem_addr;
    logic [15:0] brx_mem_wdata;
    logic brx_mem_rw;
    logic brx_mem_valid;

    lut_mem #(
        .DEPTH(32),
        .BASE_ADDR(0)
    ) mem (
        .clk(clk),
        .addr_i(brx_mem_addr),
        .wdata_i(brx_mem_wdata),
        .rdata_i(16'h0),
        .rw_i(brx_mem_rw),
        .valid_i(brx_mem_valid),

        .addr_o(),
        .wdata_o(),
        .rdata_o(mem_btx_rdata),
        .rw_o(mem_btx_rw),
        .valid_o(mem_btx_valid));
    
    // mem --> frizzle signals, it's frizzle because that's a bus you wanna get off of 
    logic [15:0] mem_btx_rdata;
    logic mem_btx_rw;
    logic mem_btx_valid;

    bridge_tx btx (
        .clk(clk),
        
        .rdata_i(mem_btx_rdata),
        .rw_i(mem_btx_rw),
        .valid_i(mem_btx_valid),

        .ready_i(utx_btx_ready),
        .data_o(btx_utx_data),
        .valid_o(btx_utx_valid));

    logic utx_btx_ready;
    logic btx_utx_valid;
    logic [7:0] btx_utx_data;
    
    uart_tx #(.CLOCKS_PER_BAUD(868)) utx (
        .clk(clk),

        .data(btx_utx_data),
        .valid(btx_utx_valid),
        .ready(utx_btx_ready),

        .tx(txd));
endmodule

`default_nettype wire