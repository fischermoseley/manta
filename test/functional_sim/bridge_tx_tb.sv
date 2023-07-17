`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

module bridge_tx_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

// boilerplate
logic clk;
integer test_num;

// tb -> bridge_tx signals
logic [15:0] tb_btx_rdata;
logic res_ready;
logic tb_btx_valid;

// uart_tx <--> bridge_tx signals
logic [7:0] btx_utx_data;
logic btx_utx_valid;
logic btx_utx_ready;

// uart_tx -> tb signals
logic utx_tb_tx;

bridge_tx btx (
    .clk(clk),

    .rdata_i(tb_btx_rdata),
    .rw_i(1'b1),
    .valid_i(tb_btx_valid),

    .data_o(btx_utx_data),
    .ready_i(btx_utx_ready),
    .valid_o(btx_utx_valid));

uart_tx #(
    .CLOCKS_PER_BAUD(868))
    utx (
    .clk(clk),

    .data(btx_utx_data),
    .valid(btx_utx_valid),
    .busy(),
    .ready(btx_utx_ready),

    .tx(utx_tb_tx));

always begin
    #`HCP
    clk = !clk;
end

initial begin
    $dumpfile("bridge_tx.vcd");
    $dumpvars(0, bridge_tx_tb);

    // setup and reset
    clk = 0;
    test_num = 0;

    tb_btx_valid = 0;
    tb_btx_rdata = 0;
    #(10*`CP);

    /* ==== Test 1 Begin ==== */
    $display("\n=== test 1: receive 0x0123 for baseline functionality ===");
    test_num = 1;
    tb_btx_rdata = 16'h0123;
    tb_btx_valid = 1;

    #`CP;
    assert(res_ready == 0) else $fatal(0, "invalid handshake: res_ready held high for more than one clock cycle");
    tb_btx_valid = 0;

    #(100000*`CP);
    /* ==== Test 1 End ==== */

    /* ==== Test 2 Begin ==== */
    $display("\n=== test 2: receive 0x4567 for baseline functionality ===");
    test_num = 2;
    tb_btx_rdata = 16'h4567;
    tb_btx_valid = 1;

    #`CP;
    assert(res_ready == 0) else $fatal(0, "invalid handshake: res_ready held high for more than one clock cycle");
    tb_btx_valid = 0;

    #(100000*`CP);
    /* ==== Test 2 End ==== */

    /* ==== Test 3 Begin ==== */
    $display("\n=== test 3: receive 0x89AB for baseline functionality ===");
    test_num = 3;
    tb_btx_rdata = 16'h89AB;
    tb_btx_valid = 1;

    #`CP;
    assert(res_ready == 0) else $fatal(0, "invalid handshake: res_ready held high for more than one clock cycle");
    tb_btx_valid = 0;

    #(100000*`CP);
    /* ==== Test 3 End ==== */

    /* ==== Test 4 Begin ==== */
    $display("\n=== test 4: receive 0xCDEF for baseline functionality ===");
    test_num = 4;
    tb_btx_rdata = 16'hCDEF;
    tb_btx_valid = 1;

    #`CP;
    assert(res_ready == 0) else $fatal(0, "invalid handshake: res_ready held high for more than one clock cycle");
    tb_btx_valid = 0;

    #(100000*`CP);
    /* ==== Test 4 End ==== */

    $finish();
end


endmodule

`default_nettype wire