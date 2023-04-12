`default_nettype none

`define CP 10
`define HCP 5

task read_reg (
    input [15:0] addr,
    output [15:0] data,
    input string desc
    );

    block_memory_tb.tb_bc_addr = addr;
    block_memory_tb.tb_bc_rw = 0;
    block_memory_tb.tb_bc_valid = 1;
    #`CP
    block_memory_tb.tb_bc_rw = 0;
    block_memory_tb.tb_bc_valid = 0;
    while (!block_memory_tb.bc_tb_valid) #`CP;
    data = block_memory_tb.bc_tb_rdata;

    $display(" -> read  0x%h from addr 0x%h (%s)", data, addr, desc);
endtask

task write_reg(
    input [15:0] addr,
    input [15:0] data,
    input string desc
    );

    block_memory_tb.tb_bc_addr = addr;
    block_memory_tb.tb_bc_wdata = data;
    block_memory_tb.tb_bc_rw = 1;
    block_memory_tb.tb_bc_valid = 1;
    #`CP
    block_memory_tb.tb_bc_rw = 0;
    block_memory_tb.tb_bc_valid = 0;
    while (!block_memory_tb.bc_tb_valid) #`CP;

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

module block_memory_tb;

    // boilerplate
    logic clk;
    integer test_num;
    reg [15:0] read_value;

    // tb -> bram_core bus
    logic [15:0] tb_bc_addr;
    logic [15:0] tb_bc_wdata;
    logic [15:0] tb_bc_rdata;
    logic tb_bc_rw;
    logic tb_bc_valid;

    // bram_core -> tb bus
    logic [15:0] bc_tb_addr;
    logic [15:0] bc_tb_wdata;
    logic [15:0] bc_tb_rdata;
    logic bc_tb_rw;
    logic bc_tb_valid;

    // bram itself
    logic [7:0] bram_user_addr = 0;
    logic [17:0] bram_user_din = 0;
    logic [17:0] bram_user_dout;
    logic bram_user_we = 0;

    my_bram my_bram_inst(
        .clk(clk),

        .addr_i(tb_bc_addr),
        .wdata_i(tb_bc_wdata),
        .rdata_i(tb_bc_rdata),
        .rw_i(tb_bc_rw),
        .valid_i(tb_bc_valid),

        .addr_o(bc_tb_addr),
        .wdata_o(bc_tb_wdata),
        .rdata_o(bc_tb_rdata),
        .rw_o(bc_tb_rw),
        .valid_o(bc_tb_valid),

        .user_clk(clk),
        .user_addr(bram_user_addr),
        .user_din(bram_user_din),
        .user_dout(bram_user_dout),
        .user_we(bram_user_we));

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("block_memory_tb.vcd");
        $dumpvars(0, block_memory_tb);

        // setup and reset
        clk = 0;
        test_num = 0;

        tb_bc_addr = 0;
        tb_bc_rdata = 0;
        tb_bc_wdata = 0;
        tb_bc_rw = 0;
        tb_bc_valid = 0;

        bram_user_addr = 0;
        bram_user_din = 0;
        bram_user_we = 0;

        #`HCP



        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read/write from BRAM, verify ===");
        test_num = 1;
        //read_reg(0, read_value, "lmao");
        write_and_verify(0, 4, "larry_op");
        write_and_verify(1, 3, "larry_op");

        // now query what's on the the user side at address 0

        #(10*`CP);

        /* ==== Test 1 End ==== */

        $finish();
    end
endmodule

`default_nettype wire