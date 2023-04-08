`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

module bit_fifo_tb;

    //boilerplate
    logic clk;
    integer test_num;

    always begin
        #`HCP
        clk = !clk;
    end

    parameter IWIDTH = 3;
    parameter OWIDTH = 7;

    logic en;
    logic [IWIDTH-1:0] in;
    logic in_valid;
    logic [OWIDTH-1:0] out;
    logic out_valid;

    bit_fifo #(.IWIDTH(IWIDTH), .OWIDTH(OWIDTH)) bfifo (
        .clk(clk),

        .en(en),
        .in(in),
        .in_valid(in_valid),
        .out(out),
        .out_valid(out_valid));

    initial begin
        $dumpfile("bit_fifo_tb.vcd");
        $dumpvars(0, bit_fifo_tb);

        // setup and reset
        clk = 0;
        test_num = 0;
        en = 0;
        in_valid = 0;
        in = 0;
        #`HCP

        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: make sure invalid data isn't added to buffer ===");
        test_num = 1;
        en = 1;
        #(10*`CP);
        en = 0;
        /* ==== Test 1 End ==== */

        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: just throw bits at it! ===");
        test_num = 1;
        en = 1;
        in_valid = 1;
        in = 3'b101;

        #(10*`CP);
        in_valid = 0;
        en = 0;

        #(10*`CP);
        /* ==== Test 2 End ==== */
        $finish();
    end
endmodule

`default_nettype wire