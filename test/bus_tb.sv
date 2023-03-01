`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

`define SEND_MSG_BITS(MSG) \
    for(int j=0; j < $size(msg); j++) begin                 \
        char = msg[j];                                      \
        for(int i=0; i < 10; i++) begin                     \
            if (i == 0) tb_urx_rxd = 0;                            \
            else if ((i > 0) & (i < 9)) tb_urx_rxd = char[i-1];    \
            else if (i == 9) tb_urx_rxd = 1;                       \
            #(10*`CP);                                         \
        end                                                 \
    end                                                     \

module bus_tb;
    // https://www.youtube.com/watch?v=WCOAr-96bGc

    //boilerplate
    logic clk;
    logic rst;
    integer test_num;
    string msg;
    logic [7:0] char;

    // tb --> uart_rx signals
    logic tb_urx_rxd;
    uart_rx #(
        .DATA_WIDTH(8),
        .CLK_FREQ_HZ(100_000_000),
        .BAUDRATE(10_000_000)
    ) urx (
        .clk(clk),
        .rst(rst),
        .rxd(tb_urx_rxd),

        .axiod(urx_brx_axid),
        .axiov(urx_brx_axiv));

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
    logic [15:0] brx_mem_1_rdata;
    logic brx_mem_1_rw;
    logic brx_mem_1_valid;

    assign brx_mem_1_rdata = 0;

    lut_mem #(
        .DEPTH(8),
        .BASE_ADDR(0)
    ) mem_1 (
        .clk(clk),
        .addr_i(brx_mem_1_addr),
        .wdata_i(brx_mem_1_wdata),
        .rdata_i(brx_mem_1_rdata),
        .rw_i(brx_mem_1_rw),
        .valid_i(brx_mem_1_valid),

        .addr_o(mem_1_mem_2_addr),
        .wdata_o(mem_1_mem_2_wdata),
        .rdata_o(mem_1_mem_2_rdata),
        .rw_o(mem_1_mem_2_rw),
        .valid_o(mem_1_mem_2_valid));

    // mem_1 --> mem_2 signals
    logic [15:0] mem_1_mem_2_addr;
    logic [15:0] mem_1_mem_2_wdata;
    logic [15:0] mem_1_mem_2_rdata;
    logic mem_1_mem_2_rw;
    logic mem_1_mem_2_valid;

    lut_mem #(
        .DEPTH(8),
        .BASE_ADDR(8)
    ) mem_2 (
        .clk(clk),
        .addr_i(mem_1_mem_2_addr),
        .wdata_i(mem_1_mem_2_wdata),
        .rdata_i(mem_1_mem_2_rdata),
        .rw_i(mem_1_mem_2_rw),
        .valid_i(mem_1_mem_2_valid),

        .addr_o(mem_2_mem_3_addr),
        .wdata_o(mem_2_mem_3_wdata),
        .rdata_o(mem_2_mem_3_rdata),
        .rw_o(mem_2_mem_3_rw),
        .valid_o(mem_2_mem_3_valid));

    // mem_2 --> mem_3 signals
    logic [15:0] mem_2_mem_3_addr;
    logic [15:0] mem_2_mem_3_wdata;
    logic [15:0] mem_2_mem_3_rdata;
    logic mem_2_mem_3_rw;
    logic mem_2_mem_3_valid;

    lut_mem #(
        .DEPTH(8),
        .BASE_ADDR(16)
    ) mem_3 (
        .clk(clk),
        .addr_i(mem_2_mem_3_addr),
        .wdata_i(mem_2_mem_3_wdata),
        .rdata_i(mem_2_mem_3_rdata),
        .rw_i(mem_2_mem_3_rw),
        .valid_i(mem_2_mem_3_valid),

        .addr_o(mem_3_btx_addr),
        .wdata_o(mem_3_btx_wdata),
        .rdata_o(mem_3_btx_rdata),
        .rw_o(mem_3_btx_rw),
        .valid_o(mem_3_btx_valid));

    // mem_3 --> bridge_tx signals
    logic [15:0] mem_3_btx_addr;
    logic [15:0] mem_3_btx_wdata;
    logic [15:0] mem_3_btx_rdata;
    logic mem_3_btx_rw;
    logic mem_3_btx_valid;

    bridge_tx btx (
        .clk(clk),
        .axiod(btx_utx_axid),
        .axiov(btx_utx_axiv),
        .axior(btx_utx_axir),

        .res_data(mem_3_btx_rdata),
        .res_valid(mem_3_btx_valid),
        .res_ready());

    // bridge_tx --> uart_tx signals
    logic [7:0] btx_utx_axid;
    logic btx_utx_axiv;
    logic btx_utx_axir;

    uart_tx #(
        .DATA_WIDTH(8),
        .CLK_FREQ_HZ(100_000_000),
        .BAUDRATE(10_000_000)
    ) utx (
        .clk(clk),
        .rst(rst),

        .axiid(btx_utx_axid),
        .axiiv(btx_utx_axiv),
        .axiir(btx_utx_axir),
        .txd(utx_tb_txd));

    // utx --> tb signals
    logic utx_tb_txd;

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("bus.vcd");
        $dumpvars(0, bus_tb);

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
        mem_1.mem[0] = 16'h0000;
        mem_1.mem[1] = 16'h0001;
        mem_1.mem[2] = 16'h0002;
        mem_1.mem[3] = 16'h0003;
        mem_1.mem[4] = 16'h0004;
        mem_1.mem[5] = 16'h0005;
        mem_1.mem[6] = 16'h0006;
        mem_1.mem[7] = 16'h0007;

        mem_2.mem[0] = 16'h0008;
        mem_2.mem[1] = 16'h0009;
        mem_2.mem[2] = 16'h000A;
        mem_2.mem[3] = 16'h000B;
        mem_2.mem[4] = 16'h000C;
        mem_2.mem[5] = 16'h000D;
        mem_2.mem[6] = 16'h000E;
        mem_2.mem[7] = 16'h000F;

        mem_3.mem[0] = 16'h0010;
        mem_3.mem[1] = 16'h0011;
        mem_3.mem[2] = 16'h0012;
        mem_3.mem[3] = 16'h0013;
        mem_3.mem[4] = 16'h0014;
        mem_3.mem[5] = 16'h0015;
        mem_3.mem[6] = 16'h0016;
        mem_3.mem[7] = 16'h0017;
        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read from 0x0001 for baseline functionality ===");
        test_num = 1;

        #(10*`CP);
        /* ==== Test 1 End ==== */

        msg = {"M12345678", 8'h0D, 8'h0A};
        `SEND_MSG_BITS(msg)

        #(1000*`CP)

        $finish();
    end
endmodule

`default_nettype wire