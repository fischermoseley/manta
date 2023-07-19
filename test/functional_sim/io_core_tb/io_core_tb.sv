`default_nettype none

`define CP 10
`define HCP 5

module io_core_tb;

    // boilerplate
    logic clk;
    integer test_num;

    // inputs
    logic picard;
    logic [6:0] data;
    logic [9:0] laforge;
    logic troi;

    // outputs
    logic kirk;
    logic [4:0] spock;
    logic [2:0] uhura;
    logic chekov;

    // tb -> io bus
    logic [15:0] tb_io_addr;
    logic [15:0] tb_io_data;
    logic tb_io_rw;
    logic tb_io_valid;

    // la -> io bus
    logic [15:0] la_tb_addr;
    logic [15:0] la_tb_data;
    logic la_tb_rw;
    logic la_tb_valid;


    io_core #(.BASE_ADDR(0)) io(
        .clk(clk),

        // inputs
        .picard(picard),
        .data(data),
        .laforge(laforge),
        .troi(troi),

        // outputs
        .kirk(kirk),
        .spock(spock),
        .uhura(uhura),
        .chekov(chekov),

        // input port
        .addr_i(tb_io_addr),
        .data_i(tb_io_data),
        .rw_i(tb_io_rw),
        .valid_i(tb_io_valid),

        // output port
        .addr_o(la_tb_addr),
        .data_o(la_tb_data),
        .rw_o(la_tb_rw),
        .valid_o(la_tb_valid));

    always begin
        #`HCP
        clk = !clk;
    end

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

        picard = 0;
        data = 0;
        laforge = 0;
        troi = 0;

        #`HCP
        #(10*`CP);

        /* ==== Test 1 Begin ==== */
        $display("\n=== test 1: read state register ===");
        test_num = 1;

        tb_io_addr = 0;
        tb_io_valid = 1;
        #`CP
        tb_io_valid = 0;
        while (!la_tb_valid) #`CP;
        $display(" -> read  0x%h from state reg (addr 0x0000)", la_tb_data);


        #(10*`CP);
        /* ==== Test 1 End ==== */

        $finish();
    end
endmodule

`default_nettype wire