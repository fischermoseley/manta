`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

`define SEND_MSG_BITS(MSG) \
    for(int j=0; j < $size(msg); j++) begin                         \
        char = msg[j];                                              \
        for(int i=0; i < 10; i++) begin                             \
            if (i == 0) tb_urx_rxd = 0;                             \
            else if ((i > 0) & (i < 9)) tb_urx_rxd = char[i-1];     \
            else if (i == 9) tb_urx_rxd = 1;                        \
            #(868*`CP);                                              \
        end                                                         \
    end                                                             \

module bus_fix_tb;
    // https://www.youtube.com/watch?v=WCOAr-96bGc

    //boilerplate
    logic clk;
    logic rst;
    integer test_num;
    string msg;
    logic [7:0] char;

    parameter CLOCKS_PER_BAUD = 10;

    // tb --> uart_rx signals
    logic tb_urx_rxd;
    rx_uart #(.CLOCKS_PER_BAUD(CLOCKS_PER_BAUD)) urx (
        .i_clk(clk),
        .i_uart_rx(tb_urx_rxd),
        .o_wr(urx_brx_axiv),
        .o_data(urx_brx_axid));

    // uart_rx --> bridge_rx signals
    logic [7:0] urx_brx_axid;
    logic urx_brx_axiv;

    bridge_rx brx (
        .clk(clk),

        .rx_data(urx_brx_axid),
        .rx_valid(urx_brx_axiv),

        .addr_o(brx_mem_addr),
        .wdata_o(brx_mem_wdata),
        .rw_o(brx_mem_rw),
        .valid_o(brx_mem_valid));

    // bridge_rx --> mem signals
    logic [15:0] brx_mem_addr;
    logic [15:0] brx_mem_wdata;
    logic brx_mem_rw;
    logic brx_mem_valid;

    lut_mem #(
        .DEPTH(32),
        .BASE_ADDR(0)
    ) ram (
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

    uart_tx #(.CLOCKS_PER_BAUD(CLOCKS_PER_BAUD)) utx (
        .clk(clk),

        .data(btx_utx_data),
        .valid(btx_utx_valid),
        .ready(utx_btx_ready),

        .tx(utx_tb_tx));

    // utx --> tb signals
    logic utx_tb_tx;

    // decoder for lolz
    logic [7:0] tb_decoder_data;
    logic [7:0] decoded_uart;
    logic tb_decoder_valid;

    rx_uart #(.CLOCKS_PER_BAUD(CLOCKS_PER_BAUD)) decoder (
        .i_clk(clk),

        .i_uart_rx(utx_tb_tx),
        .o_wr(tb_decoder_valid),
        .o_data(tb_decoder_data));

    always @(posedge clk) if (tb_decoder_valid) decoded_uart <= tb_decoder_data;

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("bus_fix.vcd");
        $dumpvars(0, bus_fix_tb);

        // setup and reset
        clk = 0;
        rst = 0;
        tb_urx_rxd = 1;
        test_num = 0;
        #`CP
        rst = 1;
        #`CP
        rst = 0;
        #`HCP

        // throw some nonzero data in the memories just so we know that we're pulling from the right ones

        for(int i=0; i< 32; i++) mem.mem[i] = i;

        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: write 0x5678 to 0x1234 for baseline functionality ===");
        test_num = 1;
        msg = {"M1234", 8'h0D, 8'h0A};
        `SEND_MSG_BITS(msg)

        #(10*`CP);
        /* ==== Test 1 End ==== */

        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: read from 0x0001 for baseline functionality ===");
        test_num = 2;
        msg = {"M1234", 8'h0D, 8'h0A};
        `SEND_MSG_BITS(msg)

        #(1000*`CP);
        /* ==== Test 2 End ==== */

        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: 100 sequential reads, stress test ===");
        test_num = 3;

        for(int i=0; i<100; i++) begin
            msg = {"M1234", 8'h0D, 8'h0A};
            `SEND_MSG_BITS(msg);
        end


        // big reads
        // for(logic[15:0] j=0; j<10; j++) begin
        //     msg = {$sformatf("M%H", j), 8'h0D, 8'h0A};
        //     `SEND_MSG_BITS(msg)
        // end

        // for(logic[15:0] j=0; j<10; j++) begin
        //     msg = {$sformatf("M%H", j), 8'h0D, 8'h0A};
        //     `SEND_MSG_BITS(msg)
        // end


        #(10*`CP);
        /* ==== Test 3 End ==== */

        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: 100 sequential writes, stress test ===");
        test_num = 4;

        for(int i=0; i<100; i++) begin
            msg = {"M12345678", 8'h0D, 8'h0A};
            `SEND_MSG_BITS(msg);
        end

        /* ==== Test 4 End ==== */

        /* ==== Test 5 Begin ==== */
        $display("\n=== test 5: 100 sequential reads, stress test ===");
        test_num = 5;

        for(int i=0; i<100; i++) begin
            msg = {"M1234", 8'h0D, 8'h0A};
            `SEND_MSG_BITS(msg);
        end

        /* ==== Test 5 End ==== */



        #(1000*`CP)

        $finish();
    end
endmodule

`default_nettype wire