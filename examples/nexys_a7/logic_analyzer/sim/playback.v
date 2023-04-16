/*
This playback module was generated with Manta v0.0.0 on 16 Apr 2023 at 14:13:24 by fischerm

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
    .clk(clk),
    .enable(1'b1),

    .larry(larry),
    .curly(curly),
    .moe(moe),
    .shemp(shemp));

*/


module my_logic_analyzer_playback (
    input wire clk,

    input wire enable,
    output reg done,

    output reg larry,
    output reg curly,
    output reg moe,
    output reg [3:0] shemp);

    parameter MEM_FILE = "";
    localparam SAMPLE_DEPTH = 4096;
    localparam TOTAL_PROBE_WIDTH = 7;

    reg [TOTAL_PROBE_WIDTH-1:0] capture [SAMPLE_DEPTH-1:0];
    reg [$clog2(SAMPLE_DEPTH)-1:0] addr;
    reg [TOTAL_PROBE_WIDTH-1:0] sample;

    assign done = (addr >= SAMPLE_DEPTH);

    initial begin
        $display("Loading capture from %s", MEM_FILE);
        $readmemb(MEM_FILE, capture, 0, SAMPLE_DEPTH-1);
        addr = 0;
    end

    always @(posedge clk) begin
        if (enable && !done) begin
            addr = addr + 1;
            sample = capture[addr];
            {shemp, moe, curly, larry} = sample;
        end
    end
endmodule