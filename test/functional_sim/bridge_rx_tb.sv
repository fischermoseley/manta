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

`define TEST_GOOD_READ_MSG(MESSAGE, ADDR) \
    tb_brx_valid = 1; \
    for(int i=0; i < $size(MESSAGE); i++) begin \
        tb_brx_data = MESSAGE[i]; \
        if(brx_tb_valid) begin \
            assert(brx_tb_addr == ADDR) else $error("wrong addr!"); \
            assert(brx_tb_rw == 0) else $error("wrong rw!");        \
            assert(brx_tb_data == 0) else $error("wrong data!");    \
        end \
        #`CP; \
    end \
    tb_brx_valid = 0; \

`define TEST_GOOD_WRITE_MSG(MESSAGE, ADDR, DATA) \
    tb_brx_valid = 1; \
    for(int i=0; i < $size(MESSAGE); i++) begin \
        tb_brx_data = MESSAGE[i]; \
        if(brx_tb_valid) begin \
            assert(brx_tb_addr == ADDR) else $error("wrong addr!"); \
            assert(brx_tb_rw == 1) else $error("wrong rw!");        \
            assert(brx_tb_data == DATA) else $error("wrong data!"); \
        end \
        #`CP; \
    end \
    tb_brx_valid = 0; \

`define TEST_BAD_MSG(MESSAGE) \
    tb_brx_valid = 1; \
    for(int i=0; i < $size(MESSAGE); i++) begin \
        tb_brx_data = MESSAGE[i]; \
        assert(brx_tb_valid == 0) else $error("wrong valid!"); \
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

    $display("\n=== test 1: transmit W12345678(CR)(LF) for baseline functionality ===");
    test_num = 1;
    message = {"W12345678", 8'h0D, 8'h0A};
    `TEST_GOOD_WRITE_MSG(message, 16'h1234, 16'h5678)
    #(10*`CP);

    $display("\n=== test 2: transmit WDEADBEEF(CR)(LF) for proper state reset ===");
    test_num = 2;
    message = {"WDEADBEEF", 8'h0D, 8'h0A};
    `TEST_GOOD_WRITE_MSG(message, 16'hDEAD, 16'hBEEF)
    #(10*`CP);

    $display("\n=== test 3: transmit RBABE(CR)(LF) for baseline functionality ===");
    test_num = 3;
    message = {"RBABE", 8'h0D, 8'h0A};
    `TEST_GOOD_READ_MSG(message, 16'hBABE);
    #(10*`CP);

    $display("\n=== test 4: transmit R0000(CR) for EOL insensitivity ===");
    test_num = 4;
    message = {"R0000", 8'h0D};
    `TEST_GOOD_READ_MSG(message, 16'hBABE);
    #(10*`CP);

    $display("\n=== test 5: transmit R1234(LF) for EOL insensitivity ===");
    test_num = 5;
    message = {"R1234", 8'h0D};
    `TEST_GOOD_READ_MSG(message, 16'h1234);
    #(10*`CP);

    $display("\n=== test 6: transmit WF00DBEEF(CR) for EOL insensitivity ===");
    test_num = 6;
    message = {"WF00DBEEF", 8'h0D};
    `TEST_GOOD_WRITE_MSG(message, 16'hF00D, 16'hBEEF);
    #(10*`CP);

    $display("\n=== test 7: transmit WB0BACAFE(LF) for EOL insensitivity ===");
    test_num = 7;
    message = {"WB0BACAFE", 8'h0D};
    `TEST_GOOD_WRITE_MSG(message, 16'hB0BA, 16'hCAFE)
    #(10*`CP);

    $display("\n\nIntentionally bad messages:");
    $display("\n=== test 8: transmit RABC(CR)(LF) for message length ===");
    test_num = 8;
    message = {"RABC", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message);
    #(10*`CP);

    $display("\n=== test 9: transmit R12345(CR)(LF) for message length ===");
    test_num = 9;
    message = {"RABC", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $display("\n=== test 10: transmit M(CR)(LF) for message length ===");
    test_num = 10;
    message = {"WABC", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $display("\n=== test 11: transmit W123456789101112131415161718191201222(CR)(LF) for message length ===");
    test_num = 11;
    message = {"W123456789101112131415161718191201222", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $display("\n=== test 12: transmit RABCG(CR)(LF) for invalid characters ===");
    test_num = 12;
    message = {"RABCG", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $display("\n=== test 13: transmit WABC[]()##*@(CR)(LF) for invalid characters and message length ===");
    test_num = 13;
    message = {"WABC[]()##*@", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $display("\n=== test 14: transmit R(CR)(LF) for message length ===");
    test_num = 14;
    message = {"R", 8'h0D, 8'h0A};
    `TEST_BAD_MSG(message)
    #(10*`CP);

    $finish();
end


endmodule
`default_nettype wire