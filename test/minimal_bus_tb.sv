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
            #(10*`CP);                                              \
        end                                                         \
    end                                                             \

module minimal_bus_tb;
    // https://www.youtube.com/watch?v=WCOAr-96bGc

    //boilerplate
    logic clk;
    logic rst;
    integer test_num;
    string msg;
    logic [7:0] char;


    // tb --> uart_rx signals
    logic tb_urx_rxd;
    rx_uart #(.CLOCKS_PER_BAUD(10)) urx (
        .i_clk(clk),
        .i_uart_rx(tb_urx_rxd),
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

        .addr_o(mem_btx_addr),
        .wdata_o(mem_btx_wdata),
        .rdata_o(mem_btx_rdata),
        .rw_o(mem_btx_rw),
        .valid_o(mem_btx_valid));
    
    // mem --> bridge_tx signals
    logic [15:0] mem_btx_addr;
    logic [15:0] mem_btx_wdata;
    logic [15:0] mem_btx_rdata;
    logic mem_btx_rw;
    logic mem_btx_valid;

    bridge_tx btx (
        .clk(clk),

        .res_data(mem_btx_rdata),
        .res_valid(mem_btx_valid),
        .res_ready(),

        .axiod(btx_utx_axid),
        .axiov(btx_utx_axiv),
        .axior(~btx_utx_axib));

    // bridge_tx --> uart_tx signals
    logic [7:0] btx_utx_axid;
    logic btx_utx_axiv;
    logic btx_utx_axib;

    tx_uart #(.CLOCKS_PER_BAUD(10)) utx(
        .i_clk(clk),
        .i_wr(btx_utx_axiv),
        .i_data(btx_utx_axid),

        .o_uart_tx(utx_tb_txd),
        .o_busy(btx_utx_axib));

    // utx --> tb signals
    logic utx_tb_txd;

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("minimal_bus.vcd");
        $dumpvars(0, minimal_bus_tb);

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
        $display("\n=== test 3: read from 0x0000-0x0007 for baseline functionality ===");
        test_num = 3;

        for(logic[15:0] j=0; j<32; j++) begin
            $display($sformatf("M%H", j));
            msg = {$sformatf("M%H", j), 8'h0D, 8'h0A};
            `SEND_MSG_BITS(msg)
        end

        #(10*`CP);
        /* ==== Test 3 End ==== */

        
        #(1000*`CP)

        $finish();
    end
endmodule

`default_nettype wire