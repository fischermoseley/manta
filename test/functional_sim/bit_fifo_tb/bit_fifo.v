`default_nettype none
`timescale 1ns/1ps

module bit_fifo(
    input wire clk,

    input wire en,
    input wire [IWIDTH-1:0] in,
    input wire in_valid,
    output reg [OWIDTH-1:0] out,
    output reg out_valid);

    parameter IWIDTH = 0;
    parameter OWIDTH = 0;

    localparam BWIDTH = OWIDTH-1 + IWIDTH;

    reg [OWIDTH-1:0] buffer;
    reg [$clog2(OWIDTH)-1:0] buffer_size;

    initial begin
        buffer = 0;
        buffer_size = 0;
        out = 0;
        out_valid = 0;
    end

    reg [OWIDTH-1:0] mask;
    reg [OWIDTH-1:0] top_half;
    reg [OWIDTH-1:0] bottom_half;
    reg [OWIDTH-1:0] joined_halves;

    always @(*) begin
        mask = (1 << buffer_size) - 1;
        top_half = (buffer & mask) << (OWIDTH - buffer_size);
        bottom_half = in >> (IWIDTH- (OWIDTH - buffer_size));
        joined_halves = top_half | bottom_half;
    end

    always @(posedge clk) begin
        out_valid <= 0;

        // RUN state
        if(en && in_valid) begin
            // this module should spit out values as soon as it's able,
            // so if we'll have enough once the present value's clocked in,
            // then we'll need to immediately assign the output as a combination
            // of what's in the buffer and what's on the line.

            if(buffer_size + IWIDTH >= OWIDTH) begin
                // compute buffer size
                //   -> everything that was in the buffer is now in the output,
                //      so what we put back in the buffer is purely what's left over
                //      from our input data once we've sliced out what we need
                buffer_size <= buffer_size + IWIDTH - OWIDTH;

                // compute buffer contents
                buffer <= ( (1 << (buffer_size + IWIDTH - OWIDTH)) - 1 ) & in;

                /*
                $display("buffer_size: %h  in: %b  ", buffer_size, in);
                $display("   buffer:      %b", buffer);
                $display("   mask:        %b", mask);
                $display("   top_half:    %b", top_half);
                $display("   bottom_half: %b", bottom_half);
                $display("   out:         %b \n", joined_halves);
                */

                // compute output
                out <= joined_halves;
                out_valid <= 1;
            end

            else begin
                // shift into the right side of the buffer
                buffer <= {buffer[BWIDTH-1-IWIDTH:0], in};
                buffer_size <= buffer_size + IWIDTH;
            end
        end

        // FLUSH state
        else if(buffer_size > 0) begin
            out <= (buffer) & ((1 << buffer_size) - 1);
            out_valid <= 1;
            buffer_size <= 0;
        end
    end
endmodule

`default_nettype wire