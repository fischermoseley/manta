`default_nettype none
`timescale 1ns/1ps

module manta(
    input wire clk,
    input wire rst,
    input wire rxd,
    output reg txd
);

    // tb --> uart_rx signals
    // uart_rx #(
    //     .DATA_WIDTH(8),
    //     .CLK_FREQ_HZ(100_000_000),
    //     .BAUDRATE(115200)
    // ) urx (
    //     .clk(clk),
    //     .rst(rst),
    //     .rxd(rxd),

    //     .axiod(urx_brx_axid),
    //     .axiov(urx_brx_axiv));
    
    rxuart urx(
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

        .req_addr(brx_mem_1_addr),
        .req_data(brx_mem_1_wdata),
        .req_rw(brx_mem_1_rw),
        .req_valid(brx_mem_1_valid),
        .req_ready(1'b1));

    // bridge_rx --> mem_1 signals
    logic [15:0] brx_mem_1_addr;
    logic [15:0] brx_mem_1_wdata;
    logic brx_mem_1_rw;
    logic brx_mem_1_valid;

    lut_mem #(
        .DEPTH(8),
        .BASE_ADDR(0)
    ) mem_1 (
        .clk(clk),
        .addr_i(brx_mem_1_addr),
        .wdata_i(brx_mem_1_wdata),
        .rdata_i(0),
        .rw_i(brx_mem_1_rw),
        .valid_i(brx_mem_1_valid),

        .addr_o(),
        .wdata_o(),
        .rdata_o(mem_1_btx_rdata),
        .rw_o(),
        .valid_o(mem_1_btx_valid));

    logic [15:0] mem_1_btx_rdata;
    logic mem_1_btx_valid;

    bridge_tx btx (
        .clk(clk),

        .res_data(mem_1_btx_rdata),
        .res_valid(mem_1_btx_valid),
        .res_ready(),

        .axiod(btx_utx_axid),
        .axiov(btx_utx_axiv),
        .axior(btx_utx_axir));

    // bridge_tx --> uart_tx signals
    logic [7:0] btx_utx_axid;
    logic btx_utx_axiv;
    logic btx_utx_axir;

    uart_tx #(
        .DATA_WIDTH(8),
        .CLK_FREQ_HZ(100_000_000),
        .BAUDRATE(115200)
    ) utx (
        .clk(clk),
        .rst(rst),

        .axiid(btx_utx_axid),
        .axiiv(btx_utx_axiv),
        .axiir(btx_utx_axir),
        
        .txd(txd));

endmodule

`default_nettype wire