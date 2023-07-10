`default_nettype none
`timescale 1ns/1ps

module uart_rx (
    input wire clk,

    input wire rx,

    output reg [7:0] data_o,
    output reg valid_o);

    parameter CLOCKS_PER_BAUD = 0;

    initial data_o = 0;
    initial valid_o = 0;

    reg [$clog2(CLOCKS_PER_BAUD)-1:0] baud_counter = 0;
    reg [7:0] buffer = 0;
    reg [3:0] bit_index = 0;

    reg prev_rx = 1;
    reg busy = 0;

    always @(posedge clk) begin
        prev_rx <= rx;
        valid_o <= 0;

        if (!busy) begin
            if (prev_rx && !rx) begin
                busy <= 1;
            end
        end

        else begin
            // run baud counter
            baud_counter <= (baud_counter < CLOCKS_PER_BAUD-1) ? baud_counter + 1 : 0;

            // sample rx in the middle of a baud period
            if (baud_counter == (CLOCKS_PER_BAUD/2) - 2) begin

                // fill buffer until end of byte on the wire
                if(bit_index <= 8) begin
                    buffer <= {rx, buffer[7:1]};
                    bit_index = bit_index + 1;
                end

                else begin
                    // reset system state
                    busy <= 0;
                    baud_counter <= 0;
                    bit_index <= 0;

                    // output word if stop bit received
                    if(rx) begin
                        data_o <= buffer;
                        valid_o <= 1;
                    end
                end
            end
        end






    end

endmodule
`default_nettype wire