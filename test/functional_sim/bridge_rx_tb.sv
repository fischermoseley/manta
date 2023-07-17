`default_nettype none
// `timescale 1ns/1ps

`define CP 10
`define HCP 5

task test_good_read_msg (
    input string message,
    input [15:0] addr
    );

    bridge_rx_tb.tb_brx_valid = 1;
    for(int i=0; i < $size(message); i++) begin
        bridge_rx_tb.tb_brx_data = message [i];
        if(bridge_rx_tb.brx_tb_valid) begin
            assert(bridge_rx_tb.brx_tb_addr == addr) else $fatal(0, "wrong addr!");
            assert(bridge_rx_tb.brx_tb_rw == 0) else $fatal(0, "wrong rw!");
            assert(bridge_rx_tb.brx_tb_data == 0) else $fatal(0, "wrong data!");
        end
        #`CP;
    end
    bridge_rx_tb.tb_brx_valid = 0;
endtask

task test_good_write_msg (
    input string message,
    input [15:0] addr,
    input [15:0] data
    );

    bridge_rx_tb.tb_brx_valid = 1;
    for(int i=0; i < $size(message); i++) begin
        bridge_rx_tb.tb_brx_data = message[i];
        if(bridge_rx_tb.brx_tb_valid) begin
            assert(bridge_rx_tb.brx_tb_addr == addr) else $fatal(0, "wrong addr!");
            assert(bridge_rx_tb.brx_tb_rw == 1) else $fatal(0, "wrong rw!");
            assert(bridge_rx_tb.brx_tb_data == data) else $fatal(0, "wrong data!");
        end
        #`CP;
    end
    bridge_rx_tb.tb_brx_valid = 0;
endtask

task test_bad_msg (
    input string message
    );

    bridge_rx_tb.tb_brx_valid = 1;
    for(int i=0; i < $size(message); i++) begin
        bridge_rx_tb.tb_brx_data = message[i];
        assert(bridge_rx_tb.brx_tb_valid == 0) else $fatal(0, "wrong valid!");
        #`CP;
    end
    bridge_rx_tb.tb_brx_valid = 0;
endtask


module bridge_rx_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

//boilerplate
logic clk;
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

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit W12345678(CR)(LF) for baseline functionality ===", test_num);
    test_good_write_msg("W12345678\r\n", 16'h1234, 16'h5678);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit WDEADBEEF(CR)(LF) for proper state reset ===", test_num);
    test_good_write_msg("WDEADBEEF\r\n", 16'hDEAD, 16'hBEEF);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit RBABE(CR)(LF) for baseline functionality ===", test_num);
    test_good_read_msg("RBABE\r\n", 16'hBABE);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit R0000(CR) for EOL insensitivity ===", test_num);
    test_good_read_msg("R0000\r", 16'hBABE);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit R1234(LF) for EOL insensitivity ===", test_num);
    test_good_read_msg("R1234\n", 16'h1234);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit WF00DBEEF(CR) for EOL insensitivity ===", test_num);
    test_good_write_msg("WF00DBEEF\r", 16'hF00D, 16'hBEEF);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit WB0BACAFE(LF) for EOL insensitivity ===", test_num);
    test_good_write_msg("WB0BACAFE\r", 16'hB0BA, 16'hCAFE);
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit R1234(LF)R5678 for back-to-back messages ===", test_num);
    test_good_read_msg("R1234\r\n", 16'h1234);
    test_good_read_msg("R5678\r\n", 16'h5678);
    #(10*`CP);

    $display("\n\nIntentionally bad messages:");

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit RABC(CR)(LF) for message length ===", test_num);
    test_bad_msg("RABC\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit R12345(CR)(LF) for message length ===", test_num);
    test_bad_msg("R12345\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit M(CR)(LF) for message length ===", test_num);
    test_bad_msg("WABC\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit W123456789101112131415161718191201222(CR)(LF) for message length ===", test_num);
    test_bad_msg("W123456789101112131415161718191201222\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit RABCG(CR)(LF) for invalid characters ===", test_num);
    test_bad_msg("RABCG\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit WABC[]()##*@(CR)(LF) for invalid characters and message length ===", test_num);
    test_bad_msg("WABC[]()##*@\r\n");
    #(10*`CP);

    test_num = test_num + 1;
    $display("\n=== test %2d: transmit R(CR)(LF) for message length ===", test_num);
    test_bad_msg("R\r\n");
    #(10*`CP);

    $finish();
end


endmodule
`default_nettype wire