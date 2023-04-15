`default_nettype none
`timescale 1ns/1ps

module replay_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic larry;
    logic curly;
    logic moe;
    logic [3:0] shemp;
    my_logic_analyzer_playback playback (
        .clk(clk),

        .enable(1'b1),
        .done(),

        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp));


    initial begin
        clk = 0;
        $dumpfile("replay_tb.vcd");
        $dumpvars(0, replay_tb);

        #(4500*5);
        $finish();
    end

endmodule



module my_logic_analyzer_playback (
    input wire clk,

    input wire enable,
    output reg done,

    output reg larry,
    output reg curly,
    output reg moe,
    output reg [3:0] shemp);

    localparam FILENAME = "capture.mem";
    localparam SAMPLE_DEPTH = 4096;
    localparam TOTAL_PROBE_WIDTH = 7;

    reg [TOTAL_PROBE_WIDTH-1:0] capture [SAMPLE_DEPTH-1:0];
    reg [$clog2(SAMPLE_DEPTH)-1:0] addr;
    reg [TOTAL_PROBE_WIDTH-1:0] sample;

    assign done = (addr >= SAMPLE_DEPTH);

    initial begin
        $display("Loading capture from %s", FILENAME);
        $readmemb(FILENAME, capture);
        addr = 0;
    end

    always @(posedge clk) begin
        if (enable && !done) begin
            addr = addr + 1;
            sample = capture[addr];
            larry = sample[0];
            curly = sample[1];
            moe = sample[2];
            shemp = sample[6:3];
        end
    end
endmodule

`default_nettype wire