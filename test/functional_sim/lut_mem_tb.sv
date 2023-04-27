`default_nettype none

`define CP 10
`define HCP 5

module lut_mem_tb;
    // https://www.youtube.com/watch?v=WCOAr-96bGc

    //boilerplate
    logic clk;
    integer test_num;

    // tb --> mem_1 signals
    logic [15:0] tb_mem_1_addr;
    logic [15:0] tb_mem_1_wdata;
    logic [15:0] tb_mem_1_rdata;
    logic tb_mem_1_rw;
    logic tb_mem_1_valid;

    lut_mem #(
        .DEPTH(8),
        .BASE_ADDR(0)
    ) mem_1 (
        .clk(clk),
        .addr_i(tb_mem_1_addr),
        .wdata_i(tb_mem_1_wdata),
        .rdata_i(tb_mem_1_rdata),
        .rw_i(tb_mem_1_rw),
        .valid_i(tb_mem_1_valid),

        .addr_o(mem_1_mem_2_addr),
        .wdata_o(mem_1_mem_2_wdata),
        .rdata_o(mem_1_mem_2_rdata),
        .rw_o(mem_1_mem_2_rw),
        .valid_o(mem_1_mem_2_valid)
    );

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
        .valid_o(mem_2_mem_3_valid)
    );

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

        .addr_o(mem_3_tb_addr),
        .wdata_o(mem_3_tb_wdata),
        .rdata_o(mem_3_tb_rdata),
        .rw_o(mem_3_tb_rw),
        .valid_o(mem_3_tb_valid)
    );

    // mem_3 --> tb signals
    logic [15:0] mem_3_tb_addr;
    logic [15:0] mem_3_tb_wdata;
    logic [15:0] mem_3_tb_rdata;
    logic mem_3_tb_rw;
    logic mem_3_tb_valid;

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("lut_mem.vcd");
        $dumpvars(0, lut_mem_tb);

        // setup and reset
        clk = 0;
        test_num = 0;
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

        tb_mem_1_addr = 0;
        tb_mem_1_wdata = 0;
        tb_mem_1_rdata = 0;
        tb_mem_1_rw = 0;
        tb_mem_1_valid = 0;

        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read from 0x0001 for baseline functionality ===");
        test_num = 1;

        // TODO: make this check that all bus outputs are 0

        // assert(req_addr == 16'h1234) else $error("incorrect addr!");
        // assert(req_data == 16'h5678) else $error("incorrect data!");
        // assert(req_rw == 1) else $error("incorrect rw!");
        // assert(bridge_rx_uut.state != bridge_rx_uut.ERROR) else $error("in error state after transmission");

        tb_mem_1_addr = 16'h0001;
        tb_mem_1_valid = 1;
        tb_mem_1_rw = 0;
        #`CP;
        tb_mem_1_valid = 0;

        #(10*`CP);
        /* ==== Test 1 End ==== */

        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: read from 0x0012 for baseline functionality ===");
        test_num = 2;

        tb_mem_1_addr = 16'h0012;
        tb_mem_1_valid = 1;
        tb_mem_1_rw = 0;
        #`CP;
        tb_mem_1_valid = 0;
        #(10*`CP);
        /* ==== Test 2 End ==== */

        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: write to 0x0012 for baseline functionality ===");
        test_num = 3;

        tb_mem_1_addr = 16'h0012;
        tb_mem_1_wdata = 16'h0069;
        tb_mem_1_valid = 1;
        tb_mem_1_rw = 1;
        #`CP;
        tb_mem_1_valid = 0;
        tb_mem_1_rw = 0;
        #(10*`CP);
        /* ==== Test 3 End ==== */

        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: read from 0x0012 for baseline functionality ===");
        test_num = 4;

        tb_mem_1_addr = 16'h000A;
        tb_mem_1_valid = 1;
        tb_mem_1_rw = 0;
        #`CP;
        tb_mem_1_valid = 0;
        #(10*`CP);
        /* ==== Test 3 End ==== */

        $finish();
    end
endmodule

`default_nettype wire