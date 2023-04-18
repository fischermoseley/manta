`default_nettype none
`timescale 1ns/1ps

module ps2_decoder(
    input wire clk,

    input wire ps2_clk,
    input wire ps2_data,

    output logic [7:0] data
    );

    reg prev_clk;
    reg [10:0] buffer = 0;
    reg [3:0] counter = 0;

    always @(posedge clk) begin
        prev_clk <= ps2_clk;

        if (!prev_clk && ps2_clk) begin
            buffer <= {buffer[9:0], ps2_data};
            counter <= counter + 1;
        end

        if (counter == 11) begin
            if (!buffer[10] && buffer[0]) begin
                counter <= 0;
                data <= {buffer[2], buffer[3], buffer[4], buffer[5], buffer[6], buffer[7], buffer[8], buffer[9]};
            end
        end

    end

endmodule

module playback_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic ps2_clk;
    logic ps2_data;

    my_logic_analyzer_playback #(.MEM_FILE("capture.mem")) my_logic_analyzer_playback_inst (
        .clk(clk),
        .enable(1'b1),

        .ps2_clk(ps2_clk),
        .ps2_data(ps2_data));

    logic [7:0] data;

    ps2_decoder decoder(
        .clk(clk),

        .ps2_clk(ps2_clk),
        .ps2_data(ps2_data),

        .data(data)
    );

    initial begin
        clk = 0;
        $dumpfile("playback_tb.vcd");
        $dumpvars(0, playback_tb);

        #(450000*5);
        $finish();
    end

endmodule





`default_nettype wire