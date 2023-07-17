`default_nettype none
`timescale 1ns/1ps

`define FPGA_MAC 48'h69_69_5A_06_54_91
`define HOST_MAC 48'h00_E0_4C_68_1E_0C
`define ETHERTYPE 16'h88_B5

module ethernet_rx_tb();

    // https://www.youtube.com/watch?v=K35qOTQLNpA
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic crsdv;
    logic [1:0] rxd;

    logic txen;
    logic [1:0] txd;

    logic [39:0] mtx_payload;
    logic mtx_start;

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

    logic [15:0] erx_addr;
    logic [15:0] erx_wdata;
    logic erx_rw;
    logic erx_valid;

    ethernet_rx #(
        .FPGA_MAC(`FPGA_MAC),
        .ETHERTYPE(`ETHERTYPE)
    ) erx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .addr_o(erx_addr),
        .wdata_o(erx_wdata),
        .rw_o(erx_rw),
        .valid_o(erx_valid));

    initial begin
        $dumpfile("ethernet_rx_tb.vcd");
        $dumpvars(0, ethernet_rx_tb);
        clk = 0;
        mtx_payload = 0;
        mtx_start = 0;
        #50;

        // try to send a read request to the bus:
        mtx_payload = 40'h01_0002_0001;
        mtx_start = 1;
        #10;
        mtx_start = 0;
        #10000;




        // for (int i=0; i<32; i=i+1) begin
        //     mtx_payload = i;
        //     mtx_start = 0;
        //     #10;
        //     mtx_start = 1;
        //     #10;
        //     mtx_start = 0;
        //     while(!mrx_valid) #10;

        //     #1000;

        //     assert(mrx_payload == i) else $fatal(0, "data mismatch!");
        // end
        $finish();
    end

endmodule
`default_nettype wire