`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

`define SEND_MESSAGE(MESSAGE) \
   rx_valid = 1; \
    for(int i=0; i < $size(MESSAGE); i++) begin \
        rx_data = MESSAGE[i]; \
        #`CP; \
    end \
    rx_valid = 0; \

module bridge_rx_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

//boilerplate
logic clk;
logic rst;
string message;
integer test_num;

// uart inputs and outputs 
logic rx;
logic [7:0] rx_data;
logic rx_valid;

// the parameter will all get filled out in manta's big instantiator thing hehehee
parameter ADDR_WIDTH = 16; // $clog2( how much memory we need rounded up to the nearest 8 )
parameter DATA_WIDTH = 16;

// request bus, gets connected to uart_rx (through a FSM)
logic [ADDR_WIDTH-1:0] addr;
logic [DATA_WIDTH-1:0] wdata;
logic rw;
logic valid;
logic req_ready;

bridge_rx bridge_rx_uut(
    .clk(clk),

    // connect to uart_rx
    .rx_data(rx_data),
    .rx_valid(rx_valid),
    
    .addr_o(addr),
    .wdata_o(wdata),
    .rw_o(rw),
    .valid_o(valid));

always begin
    #`HCP
    clk = !clk;
end

initial begin
    $dumpfile("bridge_rx.vcd");
    $dumpvars(0, bridge_rx_tb);

    // setup and reset
    clk = 0;
    rst = 0;
    rx_data = 0;
    rx_valid = 0;
    req_ready = 1;
    test_num = 0;
    #`CP
    rst = 1;
    #`CP
    rst = 0;

    /* ==== Test 1 Begin ==== */
    $display("\n=== test 1: transmit M12345678(CR)(LF) for baseline functionality ===");
    test_num = 1;
    message = {"M12345678", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(addr == 16'h1234) else $error("incorrect addr!");
    assert(wdata == 16'h5678) else $error("incorrect data!");
    assert(rw == 1) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 1 End ==== */


    /* ==== Test 2 Begin ==== */
    $display("\n=== test 2: transmit MDEADBEEF(CR)(LF) for proper state reset ===");
    test_num = 2;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MDEADBEEF", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(addr == 16'hDEAD) else $error("incorrect addr!");
    assert(wdata == 16'hBEEF) else $error("incorrect data!");
    assert(rw == 1) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 2 End ==== */


    /* ==== Test 3 Begin ==== */
    $display("\n=== test 3: transmit MBABE(CR)(LF) for baseline functionality ===");
    test_num = 3;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MBABE", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(addr == 16'hBABE) else $error("incorrect addr!");
    assert(rw == 0) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 3 End ==== */

    /* ==== Test 4 Begin ==== */
    $display("\n=== test 4: transmit M0000(CR) for EOL insensitivity ===");
    test_num = 4;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"M0000", 8'h0D};
    `SEND_MESSAGE(message)
    
    assert(addr == 16'h0000) else $error("incorrect addr!");
    assert(rw == 0) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 4 End ==== */

    /* ==== Test 5 Begin ==== */
    $display("\n=== test 5: transmit M1234(LF) for EOL insensitivity ===");
    test_num = 5;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"M1234", 8'h0D};
    `SEND_MESSAGE(message)
    
    assert(addr == 16'h1234) else $error("incorrect addr!");
    assert(rw == 0) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 5 End ==== */

    /* ==== Test 6 Begin ==== */
    $display("\n=== test 6: transmit MF00DBEEF(CR) for EOL insensitivity ===");
    test_num = 6;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MF00DBEEF", 8'h0D};
    `SEND_MESSAGE(message)
    
    assert(addr == 16'hF00D) else $error("incorrect addr!");
    assert(wdata == 16'hBEEF) else $error("incorrect data!");
    assert(rw == 1) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 6 End ==== */

    /* ==== Test 7 Begin ==== */
    $display("\n=== test 7: transmit MB0BACAFE(LF) for EOL insensitivity ===");
    test_num = 7;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MB0BACAFE", 8'h0D};
    `SEND_MESSAGE(message)
    
    assert(addr == 16'hB0BA) else $error("incorrect addr!");
    assert(wdata == 16'hCAFE) else $error("incorrect data!");
    assert(rw == 1) else $error("incorrect rw!");
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 7 End ==== */

    /* ==== Test 8 Begin ==== */
    $display("\n\nIntentionally bad messages:");
    $display("\n=== test 8: transmit MABC(CR)(LF) for message length ===");
    test_num = 8;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 8 End ==== */

    /* ==== Test 9 Begin ==== */
    $display("\n=== test 9: transmit M12345(CR)(LF) for message length ===");
    test_num = 9;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 9 End ==== */

    /* ==== Test 10 Begin ==== */
    $display("\n=== test 10: transmit M(CR)(LF) for message length ===");
    test_num = 10;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 10 End ==== */

    /* ==== Test 11 Begin ==== */
    $display("\n=== test 11: transmit M123456789101112131415161718191201222(CR)(LF) for message length ===");
    test_num = 11;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 11 End ==== */

    /* ==== Test 12 Begin ==== */
    $display("\n=== test 12: transmit MABCG(CR)(LF) for invalid characters ===");
    test_num = 12;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABCG", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 12 End ==== */

    /* ==== Test 13 Begin ==== */
    $display("\n=== test 13: transmit MABC[]()##*@(CR)(LF) for invalid characters and message length ===");
    test_num = 13;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"MABC[]()##*@", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 13 End ==== */

    /* ==== Test 14 Begin ==== */
    $display("\n=== test 14: transmit M(CR)(LF) for message length ===");
    test_num = 14;
    bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    bridge_rx_uut.bytes_received = 0;
    assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"M", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)
    
    assert(valid == 0) else $error("valid asserted for bad message");
    assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 14 End ==== */

    $finish();
end


endmodule
`default_nettype wire