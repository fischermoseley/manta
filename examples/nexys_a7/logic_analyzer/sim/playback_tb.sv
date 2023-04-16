`default_nettype none
`timescale 1ns/1ps

module playback_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic larry;
    logic curly;
    logic moe;
    logic [3:0] shemp;

    my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
        .clk(clk),
        .enable(1'b1),

        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp));


    initial begin
        clk = 0;
        $dumpfile("playback_tb.vcd");
        $dumpvars(0, playback_tb);

        #(4500*5);
        $finish();
    end

endmodule





`default_nettype wire