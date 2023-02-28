`default_nettype none
`timescale 1ns / 1ps 

module uart_rx(
    input wire clk,
    input wire rst,
    input wire rxd,

    output reg [DATA_WIDTH - 1:0] axiod,
    output reg axiov
    );
	
	parameter DATA_WIDTH = 0;
	parameter CLK_FREQ_HZ = 0;
	parameter BAUDRATE = 0;

	localparam BAUD_PERIOD = CLK_FREQ_HZ / BAUDRATE;

	reg [$clog2(BAUD_PERIOD) - 1:0] baud_counter;
	reg [$clog2(DATA_WIDTH + 2):0] bit_index;
    reg [DATA_WIDTH + 2 : 0] data_buf;

    reg prev_rxd;
    reg busy;

	always_ff @(posedge clk) begin
        prev_rxd <= rxd;
        axiov <= 0;
        baud_counter <= (baud_counter == BAUD_PERIOD - 1) ? 0 : baud_counter + 1;
	
		// reset logic
		if(rst) begin
			bit_index <= 0;
            axiod <= 0;
            busy <= 0;
            baud_counter <= 0;
		end

        // start receiving if we see a falling edge, and not already busy
        else if (prev_rxd && ~rxd && ~busy) begin
            busy <= 1;
            data_buf <= 0;
            baud_counter <= 0;
        end

        // if we're actually receiving
        else if (busy) begin
            if (baud_counter == BAUD_PERIOD / 2) begin
                data_buf[bit_index] <= rxd;
                bit_index <= bit_index + 1;

                if (bit_index == DATA_WIDTH + 1) begin
                    busy <= 0;
                    bit_index <= 0;
                    

                    if (rxd && ~data_buf[0]) begin
                        axiod <= data_buf[DATA_WIDTH : 1];
                        axiov <= 1;
                    end
                end
            end    
        end
    end

		
endmodule

`default_nettype wire