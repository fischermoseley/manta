`default_nettype none

`define CP 10
`define HCP 5

task read_reg (
    input [15:0] addr,
    output [15:0] data,
    input string desc
    );

    logic_analyzer_tb.tb_la_addr = addr;
    logic_analyzer_tb.tb_la_rw = 0;
    logic_analyzer_tb.tb_la_valid = 1;
    #`CP
    logic_analyzer_tb.tb_la_valid = 0;
    while (!logic_analyzer_tb.la_tb_valid) #`CP;
    data = logic_analyzer_tb.la_tb_rdata;

    $display(" -> read  0x%h from addr 0x%h (%s)", data, addr, desc);

    endtask

task write_reg(
    input [15:0] addr,
    input [15:0] data,
    input string desc
    );

    logic_analyzer_tb.tb_la_addr = addr;
    logic_analyzer_tb.tb_la_wdata = data;
    logic_analyzer_tb.tb_la_rw = 1;
    logic_analyzer_tb.tb_la_valid = 1;
    #`CP
    logic_analyzer_tb.tb_la_valid = 0;
    while (!logic_analyzer_tb.la_tb_valid) #`CP;

    $display(" -> wrote 0x%h to   addr 0x%h (%s)", data, addr, desc);

endtask

task write_and_verify(
    input [15:0] addr,
    input [15:0] write_data,
    input string desc
    );

    reg [15:0] read_data;

    write_reg(addr, write_data, desc);
    read_reg(addr, read_data, desc);
    assert(read_data == write_data) else $error("data read does not match data written!");
endtask

task read_all_reg();

    string desc;
    for(int i = 0; i < (logic_analyzer_tb.la.sample_mem.BASE_ADDR + logic_analyzer_tb.la.SAMPLE_DEPTH); i++) begin

        if(i == logic_analyzer_tb.la.fsm.BASE_ADDR) desc = "FSM";
        if(i == logic_analyzer_tb.la.trig_blk.BASE_ADDR) desc = "TRIG BLK";
        if(i == logic_analyzer_tb.la.sample_mem.BASE_ADDR) desc = "SAMPLE MEM";

        read_reg(i, logic_analyzer_tb.read_value, desc);
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
        $display("\n=== test 1: read/write to FSM registers, verify ===");
        test_num = 1;

        // state register
        write_and_verify(0, la.fsm.IDLE, "state reg");
        write_and_verify(0, la.fsm.FILLED, "state reg");
        write_and_verify(0, la.fsm.IDLE, "state reg");

        // trigger_loc register
        write_and_verify(1, 0, "trigger_loc reg");
        write_and_verify(1, 'h69, "trigger_loc reg");
        write_and_verify(1, 'h0612, "trigger_loc reg");

        // since we just moved the trigger location, the core has started moving into position
        // if it's functioning correctly. this means we need to reset the position and state
        // before testing the present_loc register.

        // write_and_verify(1, 0, "trigger_loc reg");
        // write_and_verify(0, 0, "state reg");

        // // present_loc register
        // write_and_verify(2, 0, "present_loc reg");
        // write_and_verify(2, 0, "present_loc reg");
        #(10*`CP);

        /* ==== Test 1 End ==== */


        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: read/write to trigger block registers, verify ===");
        test_num = 2;

        // larry
        write_and_verify(3, 0, "larry_op");
        write_and_verify(3, 2, "larry_op");
        write_and_verify(3, 0, "larry_op");

        write_and_verify(4, 0, "larry_arg");
        write_and_verify(4, 1, "larry_arg");
        write_and_verify(4, 0, "larry_arg");

        // curly
        write_and_verify(5, 0, "curly_op");
        write_and_verify(5, 3, "curly_op");
        write_and_verify(5, 0, "curly_op");

        write_and_verify(6, 0, "curly_arg");
        write_and_verify(6, 1, "curly_arg");
        write_and_verify(6, 0, "curly_arg");

        // moe
        write_and_verify(7, 0, "moe_op");
        write_and_verify(7, 5, "moe_op");
        write_and_verify(7, 0, "moe_op");

        write_and_verify(8, 0, "moe_arg");
        write_and_verify(8, 1, "moe_arg");
        write_and_verify(8, 0, "moe_arg");

        // shemp 
        write_and_verify(9, 0, "shemp_op");
        write_and_verify(9, 7, "shemp_op");
        write_and_verify(9, 0, "shemp_op");

        write_and_verify(10, 0, "shemp_arg");
        write_and_verify(10, 7, "shemp_arg");
        write_and_verify(10, 0, "shemp_arg");

        #(10*`CP);

        /* ==== Test 2 End ==== */


        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: verify FSM doesn't move out of IDLE when not running ===");
        test_num = 3;

        write_and_verify(3, 8, "larry_op");  // set operation to  eq 
        write_and_verify(4, 1, "larry_arg"); // set argument to 1

        // set larry = 1, verify core doesn't trigger
        $display(" -> set larry = 1");
        larry = 1;

        $display(" -> la core is in state 0x%h", la.fsm.state);
        assert(la.fsm.state == la.fsm.IDLE) else $error("core moved outside of IDLE state when not running!");
        
        $display(" -> wait a clock cycle");
        #`CP
        
        $display(" -> la core is in state 0x%h", la.fsm.state);
        assert(la.fsm.state == la.fsm.IDLE) else $error("core moved outside of IDLE state when not running!");

        $display(" -> set larry = 0");
        larry = 0;

        #(10*`CP);
        /* ==== Test 3 End ==== */


        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: verify FSM does move out of IDLE when running ===");
        test_num = 4;

        $display(" -> moving core to START_CAPTURE");
        write_reg(0, 1, "state");
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
        /* ==== Test 4 End ==== */

        /* ==== Test 5 Begin ==== */
        $display("\n=== test 5: change trigger to fire on shemp > 3, and verify ===");
        test_num = 5;

        write_and_verify(9, 6, "shemp_op");   // set operation to GT
        write_and_verify(10, 3, "shemp_arg"); // set argument to 3
        
        assert( (la.fsm.state == la.fsm.IDLE) || (la.fsm.state == la.fsm.FILLED) ) 
            else $error("core is running when it shouldn't be!");

        larry = 0;
        curly = 0;
        moe = 0;
        shemp = 0;
         
        write_reg(0, la.fsm.START_CAPTURE, "state");

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

        #(10*`CP);
        /* ==== Test 5 End ==== */

        $finish();
    end
endmodule

`default_nettype wire