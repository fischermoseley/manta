/*
This playback module was generated with Manta v0.0.0 on 19 Apr 2023 at 12:01:24 by fischerm

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

ether_la_playback #(.MEM_FILE("capture.mem")) ether_la_playback_inst (
    .clk(clk),
    .enable(1'b1),

    .eth_crsdv(eth_crsdv),
    .eth_rxd(eth_rxd),
    .eth_txen(eth_txen),
    .eth_txd(eth_txd));

*/


module ether_la_playback (
    input wire clk,

    input wire enable,
    output reg done,

    output reg eth_crsdv,
    output reg [1:0] eth_rxd,
    output reg eth_txen,
    output reg [1:0] eth_txd);

    parameter MEM_FILE = "";
    localparam SAMPLE_DEPTH = 17000;
    localparam TOTAL_PROBE_WIDTH = 6;

    reg [TOTAL_PROBE_WIDTH-1:0] capture [SAMPLE_DEPTH-1:0];
    reg [$clog2(SAMPLE_DEPTH)-1:0] addr;
    reg [TOTAL_PROBE_WIDTH-1:0] sample;

    assign done = (addr >= SAMPLE_DEPTH);

    initial begin
        $readmemb("capture.mem", capture, 0, SAMPLE_DEPTH-1);
        addr = 0;
    end

    always @(posedge clk) begin
        if (enable && !done) begin
            addr = addr + 1;
            sample = capture[addr];
            {eth_txd, eth_txen, eth_rxd, eth_crsdv} = sample;
        end
    end
endmodule