/*
This playback module was generated with Manta v0.0.5 on 23 Aug 2023 at 11:25:46 by fischerm

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
    .clk(clk),
    .enable(1'b1),

    .spike(spike),
    .jet(jet),
    .valentine(valentine),
    .ed(ed),
    .ein(ein));

*/


module my_logic_analyzer_playback (
    input wire clk,

    input wire enable,
    output reg done,

    output reg spike,
    output reg [1:0] jet,
    output reg [2:0] valentine,
    output reg [3:0] ed,
    output reg [4:0] ein);

    parameter MEM_FILE = "";
    localparam SAMPLE_DEPTH = 1024;
    localparam TOTAL_PROBE_WIDTH = 15;

    reg [TOTAL_PROBE_WIDTH-1:0] capture [SAMPLE_DEPTH-1:0];
    reg [$clog2(SAMPLE_DEPTH)-1:0] addr;
    reg [TOTAL_PROBE_WIDTH-1:0] sample;

    assign done = (addr >= SAMPLE_DEPTH);

    initial begin
        $readmemb(MEM_FILE, capture, 0, SAMPLE_DEPTH-1);
        addr = 0;
    end

    always @(posedge clk) begin
        if (enable && !done) begin
            addr = addr + 1;
            sample = capture[addr];
            {ein, ed, valentine, jet, spike} = sample;
        end
    end
endmodule