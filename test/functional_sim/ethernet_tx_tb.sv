`default_nettype none
//`timescale 1ns/1ps

`define FPGA_MAC 48'h69_69_5A_06_54_91
`define HOST_MAC 48'h00_E0_4C_68_1E_0C
`define ETHERTYPE 16'h88_B5

task send_on_etx_receive_on_mrx (
    input [15:0] data
    );

    ethernet_tx_tb.etx_rdata = data;
    ethernet_tx_tb.etx_rw = 0;
    ethernet_tx_tb.etx_valid = 0;
    #10;
    ethernet_tx_tb.etx_valid = 1;
    #10;
    ethernet_tx_tb.etx_valid = 0;

    while(!ethernet_tx_tb.mrx_valid) #10;

    $display(ethernet_tx_tb.mrx_payload);
endtask

module ethernet_tx_tb();

    // https://www.youtube.com/watch?v=K35qOTQLNpA
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic txen;
    logic [1:0] txd;

    // ethernet tx
    reg [15:0] etx_rdata;
    reg etx_rw;
    reg etx_valid;

    ethernet_tx #(
        .FPGA_MAC(`FPGA_MAC),
        .HOST_MAC(`HOST_MAC),
        .ETHERTYPE(`ETHERTYPE)
    ) etx (
        .clk(clk),

        .rdata_i(etx_rdata),
        .rw_i(etx_rw),
        .valid_i(etx_valid),

        .txen(txen),
        .txd(txd));

    // mac_rx, for decoding
    logic crsdv;
    logic [1:0] rxd;

    reg [55:0] mrx_payload;
    reg mrx_valid;

    mac_rx #(
        // this is the host mac since we're using mac_rx to impersonate
        // the host computer, to which packets are currently addressed.

        .FPGA_MAC(`HOST_MAC),
        .ETHERTYPE(`ETHERTYPE)
    ) mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .payload(mrx_payload),
        .valid(mrx_valid));

    logic [15:0] where_ethertype_should_be;
    logic [7:0] where_rw_should_be;
    logic [15:0] where_addr_should_be;
    logic [15:0] where_data_should_be;
    assign {where_ethertype_should_be, where_rw_should_be, where_addr_should_be, where_data_should_be} = mrx_payload;

    assign rxd = txd;
    assign crsdv = txen;

    initial begin
        $dumpfile("ethernet_tx_tb.vcd");
        $dumpvars(0, ethernet_tx_tb);
        clk = 0;
        etx_rdata = 16'h6970;
        etx_rw = 0;
        etx_valid = 0;
        #50;

        send_on_etx_receive_on_mrx(16'h6970);

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

        //     assert(mrx_payload == i) else $error("data mismatch!");
        // end
        $finish();
    end

endmodule
`default_nettype wire