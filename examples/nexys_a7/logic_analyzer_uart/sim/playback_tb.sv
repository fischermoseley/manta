`default_nettype none
`timescale 1ns/1ps

module playback_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic spike;
    logic [1:0] jet;
    logic [2:0] valentine;
    logic [3:0] ed;
    logic [4:0] ein;

    my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
        .clk(clk),
        .enable(1'b1),

        .spike(spike),
        .jet(jet),
        .valentine(valentine),
        .ed(ed),
        .ein(ein));

    initial begin
        clk = 0;
        $dumpfile("playback_tb.vcd");
        $dumpvars(0, playback_tb);

        #(450000*5);
        $finish();
    end

endmodule
`default_nettype wire