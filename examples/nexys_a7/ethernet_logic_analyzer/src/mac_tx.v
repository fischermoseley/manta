`default_nettype none
`timescale 1ns/1ps

module mac_tx(
    input wire clk,

    input wire [15:0] data,
    input wire start,

    output reg txen,
    output reg [1:0] txd
    );

    /*
    ok so how's this going to work:
    what goes on the line is either the fcs, or everything else after being routed through bitorder

    we keep the counter, once it gets to some value then we'll flip the switch and talk to the FCS

    so then we mux between:
        - the fixed portion ahead of the payload (prepayload)
        - the payload, which is some register
        - the zero padding, which is of some length that's parameterized
        - the FCS, which DOES NOT GO THROUGH BITORDER

    */


    localparam PREAMBLE = {7{8'b01010101}};
    localparam SFD = 8'b11010101;
    parameter  SRC_MAC = 48'h00_00_00_00_00_00;
    parameter  DST_MAC = 48'hFF_FF_FF_FF_FF_FF;
    parameter  LENGTH = 16'h1234;
    localparam FCS_DATA = 32'b01001110_00010000_01011001_10011010;

    localparam PREPAYLOAD_DATA = {PREAMBLE, SFD, DST_MAC, SRC_MAC, LENGTH};

    // all lengths are in units of dibits, hence all the mulitplies by four
    localparam PREPAYLOAD_LEN = (7 + 1 + 6 + 6 + 2) * 4; // in dibits
    // localparam PAYLOAD_LEN = LENGTH * 4;
    localparam PAYLOAD_LEN = 2 * 4;
    localparam ZERO_PAD_LEN = (46 * 4) - PAYLOAD_LEN ; // minimum payload size is 46 bytes
    localparam FCS_LEN = 4*4;
    localparam IPG_LEN = 96/2;

    // state machine
    reg [8:0] counter = 0;
    reg [2:0] state = 0;
    localparam IDLE = 0;
    localparam PREPAYLOAD = 1;
    localparam PAYLOAD = 2;
    localparam ZERO_PAD = 3;
    localparam FCS = 4;
    localparam IPG = 5;

    reg prev_start;
    always @(posedge clk) prev_start <= start;

    reg rst = 1;
    always @(posedge clk) rst <= 0;


    reg bitorder_axiiv;
    reg [1:0] bitorder_axiid;

    bitorder b(
        .clk(clk),
        .rst(rst),
        .axiiv(bitorder_axiiv),
        .axiid(bitorder_axiid),
        .axiov(txen),
        .axiod(txd));

    reg crc_axiiv = 0;
    reg crc_axiov;
    reg [31:0] crc_axiod;
    crc32 crc(
        .clk(clk),
        .rst(rst),

        .axiiv(crc_axiiv),
        .axiid(txd),

        .axiov(crc_axiov),
        .axiod(crc_axiod));

    always @(posedge clk) begin

        // idle state
        if (state == IDLE) begin
            bitorder_axiiv <= 0;
            bitorder_axiid <= 0;

            if(start && ~prev_start) state <= PREPAYLOAD;
            counter <= 0;
        end

        // everything before the payload (preamble, sfd, dst mac, src mac, length)
        else if (state == PREPAYLOAD) begin
            bitorder_axiiv <= 1;
            bitorder_axiid <= PREPAYLOAD_DATA[2*(PREPAYLOAD_LEN-counter)-1-:2];

            if(counter == 36) crc_axiiv <= 1;

            counter <= counter + 1;
            if(counter == PREPAYLOAD_LEN - 1) begin
                counter <= 0;
                state <= PAYLOAD;
            end
        end

        // the payload itself
        else if (state == PAYLOAD) begin
            $display(2*(PAYLOAD_LEN-counter)-2);
            bitorder_axiid <= data[2*(PAYLOAD_LEN-counter)-1-:2];

            counter <= counter + 1;
            if(counter == PAYLOAD_LEN - 1) begin
                counter <= 0;
                state <= ZERO_PAD;
            end
        end

        // zero padding
        else if (state == ZERO_PAD) begin
            bitorder_axiid <= 2'b00;

            counter <= counter + 1;
            if(counter == ZERO_PAD_LEN - 1) begin
                counter <= 0;
                state <= FCS;
            end
        end


        // readout fcs from the checksum module
        else if (state == FCS) begin
            bitorder_axiiv <= 1;
            bitorder_axiid <= FCS_DATA[2*(FCS_LEN-counter)-1-:2];

            counter <= counter + 1;
            if(counter == FCS_LEN - 1) begin
                counter <= 0;
                state <= IPG;
            end
        end

        // interpacket gap
        else if (state == IPG) begin
            bitorder_axiiv <= 0;
            bitorder_axiid <= 2'b00;

            counter <= counter + 1;
            if (counter == IPG_LEN - 1) begin
                counter <= 0;
                state <= IDLE;
            end
        end
    end
endmodule
`default_nettype wire