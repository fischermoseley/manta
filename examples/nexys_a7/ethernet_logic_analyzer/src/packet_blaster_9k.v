`default_nettype none
`timescale 1ns/1ps

module packet_blaster_9k(
    input wire clk,
    input wire rst,

    input wire [47:0] src_mac,
    input wire [47:0] dst_mac,
    input wire [15:0] data,
    input wire start,

    output reg txen,
    output reg [1:0] txd
    );

    /*
    PREAMBLE: 7 bytes
    SFD: 1 bytes
    DEST MAC: 6 bytes
    SOURCE MAC: 6 bytes
    LENGTH: 2 bytes
    DATA: 46 to 1k bytes
    FCS:4 bytes
    */

    // how long should our bus transactions be?

    /*

    coming in:
    2 bytes for address
    2 bytes for data (if writing)

    2 bytes for data (if reading)
    yeah for now let's do two and then just mask it off - only other option is trying to have some kind of buffered thing?
    but then we have to be able to handle buffering the entire ethernet MTU - which is possible, but annoying. and now we're back
    to buffering bus transactions, which was an explicit design anti-goal

    maybe for now we just do the stupid thing?

    ok so then this module should take output 2 bytes of data at the top of the packet, and then 44 bytes worth of zeros
    length is then set to 46?

    ok so plan for tomorrow is:
    - to see if we can generate the packet we want to see on scapy. verify this in wireshark
    - fire that over to the fpga, and save what it looks like with manta.

    - make sure that if we replay that back to the host through txen/txd that we get what we think we should
    - if not, then we have one FPGA transmit that packet to the other, which is recording with manta
    - if so, then just massage packet blaster 9k to produce the right output.

    */

    // all of our packets are going to be 72 bytes on wire, which is 288 dibits
    reg [8:0] counter = 0;
    reg [591:0] buffer = 0;
    reg run = 0;
    reg prev_start;

    localparam PREAMBLE = {7{8'b01010101}};
    localparam SFD = 8'b11010101;
    localparam FCS = 32'b01001110_00010000_01011001_10011010;

    bitorder b(
        .clk(clk),
        .rst(rst),
        .axiiv(run),
        .axiid(buffer[591:590]),
        .axiov(txen),
        .axiod(txd));

    always @(posedge clk) begin
        prev_start <= start;

        if (run) begin
            if (counter != 298) begin
                counter <= counter + 1;
                buffer <= {buffer[589:0], 2'b0};
            end

            else begin
                run <= 0;
            end
        end

        else begin
            if (start && ~prev_start) begin
                counter <= 0;
                run <= 1;
                buffer <= {16'b0, PREAMBLE, SFD, dst_mac, src_mac, 16'h1234, data, 352'b0, FCS};
            end
        end
    end
endmodule

`default_nettype wire