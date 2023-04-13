`timescale 1ns / 1ps
`default_nettype none

module image_sprite_tb;

    //make logics for inputs and outputs!
    logic pixel_clk_in;
    logic rst_in;
    logic [11:0] pixel_out;
    logic [10:0] hcount_in;

  image_sprite #(.WIDTH(256), .HEIGHT(256))
            uut
            ( .pixel_clk_in(pixel_clk_in),
              .rst_in(rst_in),
              .x_in(11'd256),
              .hcount_in(hcount_in),
              .y_in(10'd256),
              .vcount_in(10'd380),
              .pixel_out(pixel_out)
            );
    always begin
        #5;  //every 5 ns switch...so period of clock is 10 ns...100 MHz clock
        pixel_clk_in = !pixel_clk_in;
    end

    //initial block...this is our test simulation
    initial begin
        $dumpfile("image_sprite.vcd"); //file to store value change dump (vcd)
        $dumpvars(0,image_sprite_tb); //store everything at the current level and below
        $display("Starting Sim"); //print nice message
        pixel_clk_in = 0; //initialize clk (super important)
        rst_in = 0; //initialize rst (super important)
        hcount_in = 0;
        #10  //wait a little bit of time at beginning
        rst_in = 1; //reset system
        #10; //hold high for a few clock cycles
        rst_in=0;
        #10;
        for (hcount_in = 0; hcount_in<1025; hcount_in = hcount_in + 1)begin
          #10;
        end
        #100;
        $display("Finishing Sim"); //print nice message
        $finish;

    end
endmodule //counter_tb

`default_nettype wire
