`default_nettype none

`define CP 10
`define HCP 5

task read_reg (
        input [15:0] addr,
        output [15:0] data
        );

        logic_analyzer_tb.tb_la_addr = addr;
        logic_analyzer_tb.tb_la_rw = 0;
        logic_analyzer_tb.tb_la_valid = 1;
        #`CP
        logic_analyzer_tb.tb_la_valid = 0;
        while (!logic_analyzer_tb.la_tb_valid) #`CP;
        data = logic_analyzer_tb.la_tb_rdata;

    endtask

task write_reg(
    input [15:0] addr,
    input [15:0] data
    );

    logic_analyzer_tb.tb_la_addr = addr;
    logic_analyzer_tb.tb_la_wdata = data;
    logic_analyzer_tb.tb_la_rw = 1;
    logic_analyzer_tb.tb_la_valid = 1;
    #`CP
    logic_analyzer_tb.tb_la_valid = 0;
    while (!logic_analyzer_tb.la_tb_valid) #`CP;

endtask

task read_all_reg();
    for(int i = 0; i < (logic_analyzer_tb.la.sample_mem.BASE_ADDR + logic_analyzer_tb.la.SAMPLE_DEPTH); i++) begin

        if(i == logic_analyzer_tb.la.fsm.BASE_ADDR) $display(" -> FSM MEMORY");
        if(i == logic_analyzer_tb.la.trig_blk.BASE_ADDR) $display(" -> TRIG BLK MEMORY");
        if(i == logic_analyzer_tb.la.sample_mem.BASE_ADDR) $display(" -> SAMPLE MEM MEMORY");
        
        read_reg(i, logic_analyzer_tb.read_value);
        $display("  -> addr: 0x%h   rdata: 0x%b", i, logic_analyzer_tb.read_value);
    end
endtask

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


    logic_analyzer #(.BASE_ADDR(0), .SAMPLE_DEPTH(128)) la(
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

    reg [15:0] read_value;
    
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

        read_reg(0, read_value);
        $display(" -> read  0x%h from state reg (addr 0x0000)", read_value);

        #(10*`CP);
        /* ==== Test 1 End ==== */


        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: write to state register and verify ===");
        test_num = 2;

        write_reg(0, 5);
        $display(" -> wrote 0x0005 to state reg (addr 0x0000)");

        read_reg(0, read_value);
        $display(" -> read  0x%h from state reg (addr 0x0000)", read_value);

        write_reg(0, 0);
        $display(" -> wrote 0x0000 to state reg (addr 0x0000)");

        read_reg(0, read_value);
        $display(" -> read  0x%h from state reg (addr 0x0000)", la_tb_rdata);

        #(10*`CP);
        /* ==== Test 2 End ==== */



        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: write to trigger_loc register and verify ===");
        test_num = 3;

        write_reg(1, -16'sd69);
        $display(" -> wrote -0d69 to trigger_loc reg (addr 0x0001)");

        read_reg(1, read_value);
        $display(" -> read  0d%d from trigger_loc reg (addr 0x0001)", $signed(read_value));

        write_reg(1, 0);
        $display(" -> wrote 0x0000 to trigger_loc reg (addr 0x0001)");

        read_reg(1, read_value);
        $display(" -> read  0x%h from trigger_loc reg (addr 0x0001)", $signed(read_value));

        #(10*`CP);
        /* ==== Test 3 End ==== */



        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: configure larry_op for equality and verify ===");
        test_num = 4;

        write_reg(2, 8);
        $display(" -> wrote 0x0008 to larry_op reg (addr 0x0002)");

        read_reg(2, read_value);
        $display(" -> read  0x%h from larry_op reg (addr 0x0002)", read_value);

        #(10*`CP);
        /* ==== Test 4 End ==== */



        /* ==== Test 5 Begin ==== */
        $display("\n=== test 5: write 0x0001 to larry_arg register and verify ===");
        test_num = 5;

        write_reg(3, 1);
        $display(" -> wrote 0x0001 to larry_arg reg (addr 0x0003)");

        read_reg(3, read_value);
        $display(" -> read  0x%h from larry_arg reg (addr 0x0003)", read_value);

        #(10*`CP);
        /* ==== Test 5 End ==== */


    
        /* ==== Test 6 Begin ==== */
        $display("\n=== test 6: set larry = 1, verify core does not trigger ===");
        test_num = 6;

        $display(" -> set larry = 1");
        larry = 1; 

        $display(" -> la core is in state 0x%h", la.fsm.state);
        $display(" -> wait a clock cycle");
        #`CP
        $display(" -> la core is in state 0x%h", la.fsm.state);
        $display(" -> set larry = 0");
        larry = 0;

        #(10*`CP);
        /* ==== Test 6 End ==== */



        /* ==== Test 7 Begin ==== */
        $display("\n=== test 7: set larry = 1, verify core does trigger ===");
        test_num = 7;

        write_reg(0, 1);
        $display(" -> wrote 0x0001 to state reg (addr 0x0000)");

        #`CP

        $display(" -> set larry = 1");
        larry = 1; 

        // read
        $display(" -> la core is in state 0x%h", la.fsm.state);
        $display(" -> wait a clock cycle");
        #`CP
        $display(" -> la core is in state 0x%h", la.fsm.state);

        // run until the FILLED state is reached
        $display(" -> wait until FILLED state is reached");
        while (la.fsm.state != la.fsm.FILLED) begin
            {larry, curly, moe, shemp} = {larry, curly, moe, shemp} + 1;
            #`CP;
        end

        $display(" -> read from sample memory:");
        read_all_reg(); 

        #(200*`CP);
        /* ==== Test 7 End ==== */

        
        /* ==== Test 8 Begin ==== */
        $display("\n=== test 8: change trigger to fire on shemp > 3, and verify ===");
        test_num = 8;

        write_reg(8, 6);
        $display(" -> wrote 0x0006 to shemp_op reg (addr 0x0008)");

        read_reg(8, read_value);  
        $display(" -> read  0x%h from shemp_op reg (addr 0x0008)", la_tb_rdata);

        write_reg(9, 3);
        $display(" -> wrote 0x0003 to shemp_arg reg (addr 0x0009)");

        read_reg(9, read_value);
        $display(" -> read  0x%h from shemp_arg reg (addr 0x0009)", read_value);

        #(10*`CP);
        /* ==== Test 8 End ==== */

        /* ==== Test 9 Begin ==== */
        $display("\n=== test 9: set state machine to IDLE, verify core does not trigger ===");
        test_num = 9;

        read_reg(0, read_value);
        $display(" -> read  0x%h from state reg (addr 0x0000)", read_value);

        write_reg(0, 0);
        $display(" -> wrote 0x0000 to state reg (addr 0x0000)");

        read_reg(0, read_value);
        $display(" -> read  0x%h from state reg (addr 0x0000)", read_value);
        /* ==== Test 9 End ==== */
        
        /* ==== Test 10 Begin ==== */
        $display("\n=== test 10: set shemp = 4, verify core does trigger ===");
        test_num = 10;

        larry = 0;
        curly = 0;
        moe = 0;
        shemp = 0;

        write_reg(0, 1);
        $display(" -> wrote 0x0001 to state reg (addr 0x0000)"); 

        shemp = 4;
        $display(" -> set shemp = 4");

        // run until the FILLED state is reached
        $display(" -> wait until FILLED state is reached");
        while (la.fsm.state != la.fsm.FILLED) begin
            {larry, curly, moe, shemp} = {larry, curly, moe, shemp} + 2;
            #`CP;
        end

        $display(" -> read from sample memory:");
        read_all_reg();
         
        #(200*`CP);
        /* ==== Test 10 End ==== */

        $finish();
    end
endmodule

`default_nettype wire