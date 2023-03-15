`default_nettype none

`define CP 10
`define HCP 5

module logic_analyzer_tb;

    // boilerplate
    logic clk;
    integer test_num;

    // signal generator
    logic larry;
    logic curly;
    logic moe;
    logic [3:0] shemp;

    // tb -> la bus
    logic [15:0] tb_la_addr;
    logic [15:0] tb_la_wdata;
    logic [15:0] tb_la_rdata;
    logic tb_la_rw;
    logic tb_la_valid;

    // la -> tb bus
    logic [15:0] la_tb_addr;
    logic [15:0] la_tb_wdata;
    logic [15:0] la_tb_rdata;
    logic la_tb_rw;
    logic la_tb_valid;


    logic_analyzer la(
        .clk(clk),

        // probes
        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp),

        // input port
        .addr_i(tb_la_addr),
        .wdata_i(tb_la_wdata),
        .rdata_i(tb_la_rdata),
        .rw_i(tb_la_rw),
        .valid_i(tb_la_valid),

        // output port
        .addr_o(la_tb_addr),
        .wdata_o(la_tb_wdata),
        .rdata_o(la_tb_rdata),
        .rw_o(la_tb_rw),
        .valid_o(la_tb_valid));

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("logic_analyzer_tb.vcd");
        $dumpvars(0, logic_analyzer_tb);

        // setup and reset
        clk = 0;
        test_num = 0;

        tb_la_addr = 0;
        tb_la_rdata = 0;
        tb_la_wdata = 0;
        tb_la_rw = 0;
        tb_la_valid = 0;

        larry = 0;
        curly = 0;
        moe = 0;
        shemp = 0;
        #`HCP
        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read state register ===");
        test_num = 1;

        tb_la_addr = 0;
        tb_la_valid = 1;
        #`CP
        tb_la_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0x%h from state reg (addr 0x0000)", la_tb_rdata);


        #(10*`CP);
        /* ==== Test 1 End ==== */



        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: write to state register and verify ===");
        test_num = 2;

        // write
        tb_la_addr = 0;
        tb_la_valid = 1;
        tb_la_rw = 1;
        tb_la_wdata = 5;
        #`CP
        tb_la_valid = 0;
        #`CP
        $display(" -> wrote 0x0005 to state reg (addr 0x0000)");

        // read
        tb_la_valid = 1;
        tb_la_rw = 0;
        #`CP
        tb_la_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0x%h from state reg (addr 0x0000)", la_tb_rdata);


        #(10*`CP);
        /* ==== Test 2 End ==== */



        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: write to trigger_loc register and verify ===");
        test_num = 3;

        // write
        tb_la_addr = 1;
        tb_la_valid = 1;
        tb_la_rw = 1;
        tb_la_wdata = -16'sd69;
        #`CP
        tb_la_valid = 0;
        #`CP
        $display(" -> wrote -0d69 to trigger_loc reg (addr 0x0001)");

        // read
        tb_la_valid = 1;
        tb_la_rw = 0;
        #`CP
        tb_la_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0d%d from trigger_loc reg (addr 0x0001)", $signed(la_tb_rdata));


        #(10*`CP);
        /* ==== Test 3 End ==== */



        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: configure larry_op for equality and verify ===");
        test_num = 4;

        // write
        tb_la_addr = 2;
        tb_la_valid = 1;
        tb_la_rw = 1;
        tb_la_wdata = 8;
        #`CP
        tb_la_valid = 0;
        #`CP
        $display(" -> wrote 0x0008 to larry_op reg (addr 0x0002)");

        // read
        tb_la_valid = 1;
        tb_la_rw = 0;
        #`CP
        tb_la_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0x%h from larry_op reg (addr 0x0002)", la_tb_rdata);


        #(10*`CP);
        /* ==== Test 4 End ==== */



        /* ==== Test 5 Begin ==== */
        $display("\n=== test 5: write 0x0001 to larry_arg register and verify ===");
        test_num = 5;

        // write
        tb_la_addr = 3;
        tb_la_valid = 1;
        tb_la_rw = 1;
        tb_la_wdata = 1;
        #`CP
        tb_la_valid = 0;
        #`CP
        $display(" -> wrote 0x0001 to larry_arg reg (addr 0x0003)");

        // read
        tb_la_valid = 1;
        tb_la_rw = 0;
        #`CP
        tb_la_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0x%h from larry_arg reg (addr 0x0003)", la_tb_rdata);


        #(10*`CP);
        /* ==== Test 5 End ==== */


    
        /* ==== Test 6 Begin ==== */
        $display("\n=== test 6: set larry = 1, verify core does not trigger ===");
        test_num = 6;

        larry = 1; 
        $display(" -> set larry = 1");

        // read
        $display(" -> la core is in state 0x%h", la.state);
        #`CP
        $display(" -> la core is in state 0x%h", la.state);


        #(10*`CP);
        /* ==== Test 6 End ==== */

        $finish();
    end
endmodule

`default_nettype wire