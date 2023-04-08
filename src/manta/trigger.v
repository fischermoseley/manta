`default_nettype none
`timescale 1ns/1ps

module trigger (
    input wire clk,

    input wire [INPUT_WIDTH-1:0] probe,
    input wire [3:0] op,
    input wire [INPUT_WIDTH-1:0] arg,

    output reg trig);

    parameter INPUT_WIDTH = 0;

    localparam DISABLE = 0;
    localparam RISING = 1;
    localparam FALLING = 2;
    localparam CHANGING = 3;
    localparam GT = 4;
    localparam LT = 5;
    localparam GEQ = 6;
    localparam LEQ = 7;
    localparam EQ = 8;
    localparam NEQ = 9;

    reg [INPUT_WIDTH-1:0] probe_prev = 0;
    always @(posedge clk) probe_prev <= probe;

    always @(*) begin
        case (op)
            RISING :    trig = (probe > probe_prev);
            FALLING :   trig = (probe < probe_prev);
            CHANGING :  trig = (probe != probe_prev);
            GT:         trig = (probe > arg);
            LT:         trig = (probe < arg);
            GEQ:        trig = (probe >= arg);
            LEQ:        trig = (probe <= arg);
            EQ:         trig = (probe == arg);
            NEQ:        trig = (probe != arg);
            default:    trig = 0;
        endcase
    end
endmodule

`default_nettype wire