`default_nettype none
`timescale 1ns/1ps

`define FPGA_MAC 48'h69_69_5A_06_54_91
`define HOST_MAC 48'h00_E0_4C_68_1E_0C
`define ETHERTYPE 16'h88_B5


module mac_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic crsdv;
    logic [1:0] rxd;

    logic txen;
    logic [1:0] txd;

    // this testbench makes sure that our rx pipeline is good,
    // so we'll have mtx simulate the host machine and blast
    // 5 bytes (plus padding) onto our fake RMII
    logic [39:0] mtx_payload;
    logic mtx_start;

    logic [39:0] mrx_payload;
    logic mrx_valid;

    mac_tx #(
        .SRC_MAC(`HOST_MAC),
        .DST_MAC(`FPGA_MAC),
        .ETHERTYPE(`ETHERTYPE),
        .PAYLOAD_LENGTH_BYTES(5)
    ) mtx (
        .clk(clk),

        .payload(mtx_payload),
        .start(mtx_start),

        .txen(txen),
        .txd(txd));

    assign rxd = txd;
    assign crsdv = txen;

    mac_rx #(
        .FPGA_MAC(`FPGA_MAC),
        .ETHERTYPE(`ETHERTYPE)
    ) mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .payload(mrx_payload),
        .valid(mrx_valid));

    initial begin
        $dumpfile("mac_tb.vcd");
        $dumpvars(0, mac_tb);
        clk = 0;
        mtx_payload = 0;
        mtx_start = 0;
        #10;

        for (int i=0; i<32; i=i+1) begin
            mtx_payload = i;
            mtx_start = 0;
            #10;
            mtx_start = 1;
            #10;
            mtx_start = 0;
            while(!mrx_valid) #10;

            #1000;

            assert(mrx_payload == i) else $fatal(0, "data mismatch!");
        end
        $finish();
    end

endmodule
`default_nettype wire