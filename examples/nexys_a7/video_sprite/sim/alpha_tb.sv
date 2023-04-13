`timescale 1ns / 1ps
`default_nettype none

module alpha_tester(input wire [2:0] alpha_in,
                    input wire [11:0] a_in,
                    input wire [11:0] b_in,
                    output logic [11:0] pixel_out);

    // your (combinational) alpha blending logic goes here!
    // replace the code below with your bit math
    logic [3:0] r, g, b;
    assign r = 0;
    assign g = 0;
    assign b = 0;
    assign pixel_out = {r, g, b};
endmodule

module alpha_tb;
  logic [2:0] alpha_in;
  logic [11:0] a_in;
  logic [11:0] b_in;
  logic [11:0] pixel_out;

  alpha_tester uut (.alpha_in(alpha_in),
                    .a_in(a_in),
                    .b_in(b_in),
                    .pixel_out(pixel_out));

    //initial block...this is our test simulation
    initial begin
        $dumpfile("alpha.vcd"); //file to store value change dump (vcd)
        $dumpvars(0,alpha_tb); //store everything at the current level and below
        $display("Starting Sim"); //print nice message
        a_in = 12'hF00;
        b_in = 12'hFFF;
        alpha_in = 0;
        #10  //wait a little bit of time at beginning
        $display("a_in = %12b b_in = %12b",a_in, b_in);
        for (integer i = 0; i<5; i= i+1)begin
          alpha_in = i;
          #10;
          $display("alpha_in = %d pixel_out = %03h", alpha_in, pixel_out);
        end
        #100;
        $display("Finishing Sim"); //print nice message
        $finish;

    end
endmodule //counter_tb

`default_nettype wire