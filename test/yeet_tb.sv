`default_nettype none
`timescale 1ns/1ps

`define CP 10
`define HCP 5

module yeet_tb();
    logic clk;

    logic [15:0] tb_btx_rdata;
    logic tb_btx_rw;
    logic tb_btx_valid;

    bridge_tx btx (
        .clk(clk),

        .rdata_i(tb_btx_rdata),
        .rw_i(tb_btx_rw),
        .valid_i(tb_btx_valid),

        .ready_i(utx_btx_ready),
        .data_o(btx_utx_data),
        .valid_o(btx_utx_valid));

    logic [7:0] btx_utx_data;
    logic btx_utx_valid;
    logic utx_btx_ready;

    uart_tx #(.CLOCKS_PER_BAUD(10)) utx (
        .clk(clk),

        .data(btx_utx_data),
        .valid(btx_utx_valid),
        .ready(utx_btx_ready),
        
        .tx(utx_tb_tx));

    logic utx_tb_tx;

    logic [7:0] decoded_byte;
    logic decoder_valid;
    logic [7:0] decoder_data;

    always @(posedge clk) if (decoder_valid) decoded_byte <= decoder_data;

    rx_uart #(.CLOCKS_PER_BAUD(10)) urx_decoder(
        .i_clk(clk),

        .i_uart_rx(utx_tb_tx),
        .o_wr(decoder_valid),
        .o_data(decoder_data));

    always begin
        #`HCP
        clk = !clk;
    end

    initial begin
        $dumpfile("yeet.vcd");
        $dumpvars(0, yeet_tb);
        clk = 0;
        tb_btx_rdata = 0;
        tb_btx_valid = 0;
        tb_btx_rw = 0;
        #`HCP

        #(10*`CP);

        // put some shit on the bus
        tb_btx_rdata = 16'h69;
        tb_btx_valid = 1;
        tb_btx_rw = 0;
        #`CP
        tb_btx_valid = 0;

        // wait a bit 
        #(7000 - `CP);

        // put some more shit on the bus
        tb_btx_rdata = 16'h42;
        tb_btx_valid = 1;
        tb_btx_rw = 1;
        #`CP
        tb_btx_valid = 0;
        #(7000 - `CP);

        $finish();

    end

endmodule

`default_nettype wire