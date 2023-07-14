`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

`define SEND_MESSAGE(MESSAGE) \
    tb_brx_valid = 1; \
    for(int i=0; i < $size(MESSAGE); i++) begin \
        tb_brx_data = MESSAGE[i]; \
        #`CP; \
    end \
    tb_brx_valid = 0; \

module bridge_rx_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

//boilerplate
logic clk;
string message;
integer test_num;

// uart inputs and outputs
logic [7:0] tb_brx_data;
logic tb_brx_valid;

logic [15:0] brx_tb_addr;
logic [15:0] brx_tb_data;
logic brx_tb_rw;
logic brx_tb_valid;

bridge_rx bridge_rx_uut(
    .clk(clk),

    .data_i(tb_brx_data),
    .valid_i(tb_brx_valid),

    .addr_o(brx_tb_addr),
    .data_o(brx_tb_data),
    .rw_o(brx_tb_rw),
    .valid_o(brx_tb_valid));

always begin
    #`HCP
    clk = !clk;
end

initial begin
    $dumpfile("bridge_rx.vcd");
    $dumpvars(0, bridge_rx_tb);

    // setup and reset
    clk = 0;
    tb_brx_data = 0;
    tb_brx_valid = 0;
    test_num = 0;
    #`CP
    #`HCP

    /* ==== Test 1 Begin ==== */
    $display("\n=== test 1: transmit W12345678(CR)(LF) for baseline functionality ===");
    test_num = 1;
    message = {"W12345678", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'h1234) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_data == 16'h5678) else $error("incorrect data!");
    assert(brx_tb_rw == 1) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 1 End ==== */


    /* ==== Test 2 Begin ==== */
    $display("\n=== test 2: transmit WDEADBEEF(CR)(LF) for proper state reset ===");
    test_num = 2;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"WDEADBEEF", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'hDEAD) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_data == 16'hBEEF) else $error("incorrect data!");
    assert(brx_tb_rw == 1) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 2 End ==== */


    /* ==== Test 3 Begin ==== */
    $display("\n=== test 3: transmit RBABE(CR)(LF) for baseline functionality ===");
    test_num = 3;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"RBABE", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'hBABE) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_rw == 0) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 3 End ==== */

    /* ==== Test 4 Begin ==== */
    $display("\n=== test 4: transmit R0000(CR) for EOL insensitivity ===");
    test_num = 4;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"R0000", 8'h0D};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'h0000) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_rw == 0) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 4 End ==== */

    /* ==== Test 5 Begin ==== */
    $display("\n=== test 5: transmit R1234(LF) for EOL insensitivity ===");
    test_num = 5;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"R1234", 8'h0D};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'h1234) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_rw == 0) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 5 End ==== */

    /* ==== Test 6 Begin ==== */
    $display("\n=== test 6: transmit WF00DBEEF(CR) for EOL insensitivity ===");
    test_num = 6;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"WF00DBEEF", 8'h0D};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'hF00D) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_data == 16'hBEEF) else $error("incorrect data!");
    assert(brx_tb_rw == 1) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 6 End ==== */

    /* ==== Test 7 Begin ==== */
    $display("\n=== test 7: transmit WB0BACAFE(LF) for EOL insensitivity ===");
    test_num = 7;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"WB0BACAFE", 8'h0D};
    `SEND_MESSAGE(message)

    assert(brx_tb_addr == 16'hB0BA) else $error("incorrect brx_tb_addr!");
    assert(brx_tb_data == 16'hCAFE) else $error("incorrect data!");
    assert(brx_tb_rw == 1) else $error("incorrect brx_tb_rw!");
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

    #(10*`CP);
    /* ==== Test 7 End ==== */

    /* ==== Test 8 Begin ==== */
    $display("\n\nIntentionally bad messages:");
    $display("\n=== test 8: transmit RABC(CR)(LF) for message length ===");
    test_num = 8;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"RABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 8 End ==== */

    /* ==== Test 9 Begin ==== */
    $display("\n=== test 9: transmit R12345(CR)(LF) for message length ===");
    test_num = 9;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"RABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 9 End ==== */

    /* ==== Test 10 Begin ==== */
    $display("\n=== test 10: transmit M(CR)(LF) for message length ===");
    test_num = 10;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"WABC", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 10 End ==== */

    /* ==== Test 11 Begin ==== */
    $display("\n=== test 11: transmit W123456789101112131415161718191201222(CR)(LF) for message length ===");
    test_num = 11;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"W123456789101112131415161718191201222", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 11 End ==== */

    /* ==== Test 12 Begin ==== */
    $display("\n=== test 12: transmit RABCG(CR)(LF) for invalid characters ===");
    test_num = 12;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"RABCG", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 12 End ==== */

    /* ==== Test 13 Begin ==== */
    $display("\n=== test 13: transmit WABC[]()##*@(CR)(LF) for invalid characters and message length ===");
    test_num = 13;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"WABC[]()##*@", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 13 End ==== */

    /* ==== Test 14 Begin ==== */
    $display("\n=== test 14: transmit R(CR)(LF) for message length ===");
    test_num = 14;
    // bridge_rx_uut.state = bridge_rx_uut.ACQUIRE;
    // bridge_rx_uut.bytes_received = 0;
    // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state before transmission");
    message = {"R", 8'h0D, 8'h0A};
    `SEND_MESSAGE(message)

    assert(brx_tb_valid == 0) else $error("brx_tb_valid asserted for bad message");
    // assert(bridge_rx_uut.state == bridge_rx_uut.ERROR) else $error("not in error state after transmission");

    #(10*`CP);
    /* ==== Test 14 End ==== */

    $finish();
end


endmodule
`default_nettype wire