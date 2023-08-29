`default_nettype none

`define CP 10
`define HCP 5

task read_reg (
    input [15:0] addr,
    output [15:0] data,
    input string desc
    );

    io_core_tb.tb_io_addr = addr;
    io_core_tb.tb_io_rw = 0;
    io_core_tb.tb_io_valid = 1;
    #`CP
    io_core_tb.tb_io_valid = 0;
    while (!io_core_tb.io_tb_valid) #`CP;
    data = io_core_tb.io_tb_data;

    $display(" -> read  0x%h from addr 0x%h (%s)", data, addr, desc);
endtask

task write_reg(
    input [15:0] addr,
    input [15:0] data,
    input string desc
    );

    io_core_tb.tb_io_addr = addr;
    io_core_tb.tb_io_data = data;
    io_core_tb.tb_io_rw = 1;
    io_core_tb.tb_io_valid = 1;
    #`CP
    io_core_tb.tb_io_valid = 0;
    while (!io_core_tb.io_tb_valid) #`CP;

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
    assert(read_data == write_data) else $fatal(0, "data read does not match data written!");
endtask

// task read_all_reg();
//     string desc;
//     for(int i = 0; i < (io_core_tb.la.block_mem.MAX_ADDR); i++) begin

//         if(i == io_core_tb.la.fsm_registers.BASE_ADDR) desc = "FSM";
//         if(i == io_core_tb.la.trig_blk.BASE_ADDR) desc = "TRIG BLK";
//         if(i == io_core_tb.la.block_mem.BASE_ADDR) desc = "SAMPLE MEM";

//         read_reg(i, io_core_tb.read_value, desc);
//     end
// endtask

module io_core_tb;

    // boilerplate
    logic clk;
    integer test_num;

    // inputs
    logic probe0;
    logic [1:0] probe1;
    logic [7:0] probe2;
    logic [19:0] probe3;

    // outputs
    logic probe4;
    logic [1:0] probe5;
    logic [7:0] probe6;
    logic [19:0] probe7;

    // tb -> io bus
    logic [15:0] tb_io_addr;
    logic [15:0] tb_io_data;
    logic tb_io_rw;
    logic tb_io_valid;

    // la -> io bus
    logic [15:0] io_tb_addr;
    logic [15:0] io_tb_data;
    logic io_tb_rw;
    logic io_tb_valid;


    io_core #(.BASE_ADDR(0)) io(
        .bus_clk(clk),
        .user_clk(clk),

        // inputs
        .probe0(probe0),
        .probe1(probe1),
        .probe2(probe2),
        .probe3(probe3),

        // outputs
        .probe4(probe4),
        .probe5(probe5),
        .probe6(probe6),
        .probe7(probe7),

        // input port
        .addr_i(tb_io_addr),
        .data_i(tb_io_data),
        .rw_i(tb_io_rw),
        .valid_i(tb_io_valid),

        // output port
        .addr_o(io_tb_addr),
        .data_o(io_tb_data),
        .rw_o(io_tb_rw),
        .valid_o(io_tb_valid));

    always begin
        #`HCP
        clk = !clk;
    end

    logic [15:0] read_data;

    initial begin
        $dumpfile("io_core_tb.vcd");
        $dumpvars(0, io_core_tb);

        // setup and reset
        clk = 0;
        test_num = 0;

        tb_io_addr = 0;
        tb_io_data = 0;
        tb_io_rw = 0;
        tb_io_valid = 0;

        probe0 = 0;
        probe1 = 1;
        probe2 = 2;
        probe3 = 3;

        // #`HCP
        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read initial register states ===");
        test_num = 1;
        read_reg(0, read_data, "strobe");
        read_reg(1, read_data, "probe0");
        read_reg(2, read_data, "probe1");
        read_reg(3, read_data, "probe2");
        read_reg(4, read_data, "probe3[15:0]");
        read_reg(5, read_data, "probe3[19:16]");

        read_reg(6, read_data, "probe4");
        read_reg(7, read_data, "probe5");
        read_reg(8, read_data, "probe6");
        read_reg(9, read_data, "probe7[15:0]");
        read_reg(10, read_data, "probe7[19:16]");
        #(10*`CP);
        /* ==== Test 1 End ==== */

        /* ==== Test 2 Begin ==== */
        $display("\n=== test 2: assert input buffers initialized correctly ===");
        test_num = 2;
        read_reg(0, read_data, "strobe");
        assert(read_data == 0) else $fatal(0, "strobe does not initialize to zero!");
        assert(io.strobe == 0) else $fatal(0, "strobe does not initialize to zero!");

        read_reg(1, read_data, "probe0");
        assert(read_data == 0) else $fatal(0, "probe0_buf does not initialize to zero!");
        assert(io.probe0_buf == 0) else $fatal(0, "probe0_buf does not initialize to zero!");

        read_reg(2, read_data, "probe1");
        assert(read_data == 0) else $fatal(0, "probe1_buf does not initialize to zero!");
        assert(io.probe1_buf == 0) else $fatal(0, "probe1_buf does not initialize to zero!");

        read_reg(3, read_data, "probe2");
        assert(read_data == 0) else $fatal(0, "probe2_buf does not initialize to zero!");
        assert(io.probe2_buf == 0) else $fatal(0, "probe2_buf does not initialize to zero!");

        read_reg(4, read_data, "probe3[15:0]");
        assert(read_data == 0) else $fatal(0, "probe3_buf does not initialize to zero!");
        read_reg(5, read_data, "probe3[19:16]");
        assert(read_data == 0) else $fatal(0, "probe3_buf does not initialize to zero!");
        assert(io.probe3_buf == 0) else $fatal(0, "probe3_buf does not initialize to zero!");

        #(10*`CP);
        /* ==== Test 2 End ==== */


        /* ==== Test 3 Begin ==== */
        $display("\n=== test 3: assert outputs and output buffers initialized correctly ===");
        test_num = 3;
        read_reg(6, read_data, "probe4");
        assert(read_data == 1) else $fatal(0, "probe4 does not initialize correctly!");
        assert(io.probe4_buf == 1) else $fatal(0, "probe4_buf does not initialize correctly!");
        assert(io.probe4 == 1) else $fatal(0, "probe4 does not initialize correctly!");

        read_reg(7, read_data, "probe5");
        assert(read_data == 3) else $fatal(0, "probe5 does not initialize correctly!");
        assert(io.probe5_buf == 3) else $fatal(0, "probe5_buf does not initialize correctly!");
        assert(io.probe5 == 3) else $fatal(0, "probe5 does not initialize correctly!");

        read_reg(8, read_data, "probe6");
        assert(read_data == 6) else $fatal(0, "probe6 does not initialize correctly!");
        assert(io.probe6_buf == 6) else $fatal(0, "probe6_buf does not initialize correctly!");
        assert(io.probe6 == 6) else $fatal(0, "probe6 does not initialize correctly!");

        read_reg(9, read_data, "probe7[15:0]");
        assert(read_data == 7) else $fatal(0, "probe7 does not initialize correctly!");
        read_reg(10, read_data, "probe7[19:16]");
        assert(read_data == 0) else $fatal(0, "probe7 does not initialize correctly!");
        assert(io.probe7_buf == 7) else $fatal(0, "probe7_buf does not initialize correctly!");
        assert(io.probe7 == 7) else $fatal(0, "probe7 does not initialize correctly!");


        #(10*`CP);
        /* ==== Test 3 End ==== */

        /* ==== Test 4 Begin ==== */
        $display("\n=== test 4: write new output value to each output probe===");
        test_num = 4;
        write_reg(6, 0, "probe4");
        assert(io.probe4_buf == 0) else $fatal(0, "probe4_buf does not update correctly!");
        assert(io.probe4 != 0) else $fatal(0, "probe4 updated without strobing!");

        write_reg(7, 0, "probe5");
        assert(io.probe5_buf == 0) else $fatal(0, "probe5_buf does not update correctly!");
        assert(io.probe5 != 0) else $fatal(0, "probe5 updated without strobing!");

        write_reg(8, 0, "probe6");
        assert(io.probe6_buf == 0) else $fatal(0, "probe6_buf does not update correctly!");
        assert(io.probe6 != 0) else $fatal(0, "probe6 updated without strobing!");

        write_reg(9, 0, "probe7[15:0]");
        write_reg(10, 0, "probe7[19:16]");
        assert(io.probe7_buf == 0) else $fatal(0, "probe7_buf does not update correctly!");
        assert(io.probe7 != 0) else $fatal(0, "probe7 updated without strobing!");
        #(10*`CP);
        /* ==== Test 4 End ==== */

        /* ==== Test 5 Begin ==== */
        $display("\n=== test 5: strobe core, check that inputs and outputs updated ===");
        test_num = 5;

        write_reg(0, 1, "strobe");
        write_reg(0, 0, "strobe");

        assert(io.probe4 == 0) else $fatal(0, "probe4 did not update correctly!");
        assert(io.probe5 == 0) else $fatal(0, "probe5 did not update correctly!");
        assert(io.probe6 == 0) else $fatal(0, "probe6 did not update correctly!");
        assert(io.probe7 == 0) else $fatal(0, "probe7 did not update correctly!");

        assert(io.probe0_buf == 0) else $fatal(0, "probe0_buf did not update correctly!");
        assert(io.probe1_buf == 1) else $fatal(0, "probe1_buf did not update correctly!");
        assert(io.probe2_buf == 2) else $fatal(0, "probe2_buf did not update correctly!");
        assert(io.probe3_buf == 3) else $fatal(0, "probe3_buf did not update correctly!");
        assert(io.probe4_buf == 0) else $fatal(0, "probe4_buf did not update correctly!");
        assert(io.probe5_buf == 0) else $fatal(0, "probe5_buf did not update correctly!");
        assert(io.probe6_buf == 0) else $fatal(0, "probe6_buf did not update correctly!");
        assert(io.probe7_buf == 0) else $fatal(0, "probe7_buf did not update correctly!");
        /* ==== Test 5 End ==== */


        $finish();
    end
endmodule

`default_nettype wire