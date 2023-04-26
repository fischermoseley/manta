/*
This playback module was generated with Manta v0.0.5 on 26 Apr 2023 at 12:42:05 by fischerm

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
    .clk(clk),
    .enable(1'b1),

    .ps2_clk(ps2_clk),
    .ps2_data(ps2_data));

*/


module my_logic_analyzer_playback (
    input wire clk,

    input wire enable,
    output reg done,

    output reg ps2_clk,
    output reg ps2_data);

    parameter MEM_FILE = "";
    localparam SAMPLE_DEPTH = 64000;
    localparam TOTAL_PROBE_WIDTH = 2;

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
            {ps2_data, ps2_clk} = sample;
        end
    end
endmodule