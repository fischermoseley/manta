`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

module bridge_tx_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

//boilerplate
logic clk;
logic rst;
integer test_num;

// uart_tx <--> tb signals
logic txd;

// uart_tx <--> bridge_tx signals
logic [7:0] axid;
logic axiv;
logic axir;

// bridge_tx <--> tb signals
logic res_valid;
logic res_ready;
logic [15:0] res_data;

uart_tx #(
    .DATA_WIDTH(8),
    .CLK_FREQ_HZ(100_000_000),
    .BAUDRATE(115200))
    uart_tx_uut (
    .clk(clk),
    .rst(rst),
    .txd(txd),

    .axiid(axid),
    .axiiv(axiv),
    .axiir(axir));

bridge_tx bridge_tx_uut(
    .clk(clk),

    .axiod(axid),
    .axiov(axiv),
    .axior(axir),
    
    .res_valid(res_valid),
    .res_ready(res_ready),
    .res_data(res_data));

always begin
    #`HCP
    clk = !clk;
end

initial begin
    $dumpfile("bridge_tx.vcd");
    $dumpvars(0, bridge_tx_tb);

    // setup and reset
    clk = 0;
    rst = 0;
    test_num = 0;

    res_valid = 0;
    res_data = 0;
    #`CP
    rst = 1;
    #`CP
    rst = 0;
    #(10*`CP);

    /* ==== Test 1 Begin ==== */
    $display("\n=== test 1: receive 0x0123 for baseline functionality ===");
    test_num = 1;
    res_data = 16'h0123;
    res_valid = 1;
    
    #`CP;
    assert(res_ready == 0) else $error("invalid handshake: res_ready held high for more than one clock cycle");
    res_valid = 0;

    #(100000*`CP);
    /* ==== Test 1 End ==== */

    /* ==== Test 2 Begin ==== */
    $display("\n=== test 2: receive 0x4567 for baseline functionality ===");
    test_num = 2;
    res_data = 16'h4567;
    res_valid = 1;
    
    #`CP;
    assert(res_ready == 0) else $error("invalid handshake: res_ready held high for more than one clock cycle");
    res_valid = 0;

    #(100000*`CP);
    /* ==== Test 2 End ==== */

    /* ==== Test 3 Begin ==== */
    $display("\n=== test 3: receive 0x89AB for baseline functionality ===");
    test_num = 3;
    res_data = 16'h89AB;
    res_valid = 1;
    
    #`CP;
    assert(res_ready == 0) else $error("invalid handshake: res_ready held high for more than one clock cycle");
    res_valid = 0;

    #(100000*`CP);
    /* ==== Test 3 End ==== */

    /* ==== Test 4 Begin ==== */
    $display("\n=== test 4: receive 0xCDEF for baseline functionality ===");
    test_num = 4;
    res_data = 16'hCDEF;
    res_valid = 1;
    
    #`CP;
    assert(res_ready == 0) else $error("invalid handshake: res_ready held high for more than one clock cycle");
    res_valid = 0;

    #(100000*`CP);
    /* ==== Test 4 End ==== */

    $finish();
end


endmodule

`default_nettype wire