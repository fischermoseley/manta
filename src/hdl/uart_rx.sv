`default_nettype none
`timescale 1ns / 1ps 

module uart_rx(
    input wire clk,
    input wire rst,
    input wire rxd,

    output logic [DATA_WIDTH - 1:0] data,
    output logic ready,
    output logic busy
    );

    // Just going to stick to 8N1 for now, we'll come back and
	// parameterize this later.
	
	parameter DATA_WIDTH = 8;
	parameter CLK_FREQ_HZ = 100_000_000;
	parameter BAUDRATE = 115200;

	localparam PRESCALER = CLK_FREQ_HZ / BAUDRATE;

	logic [$clog2(PRESCALER) - 1:0] baud_counter;
	logic [$clog2(DATA_WIDTH + 2):0] bit_index;
    logic [DATA_WIDTH + 2 : 0] data_buf;

    logic prev_rxd;

	always_ff @(posedge clk) begin
        prev_rxd <= rxd;
        ready <= 0;
        baud_counter <= (baud_counter == PRESCALER - 1) ? 0 : baud_counter + 1;
	
		// reset logic
		if(rst) begin
			bit_index <= 0;
            data <= 0;
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
            if (baud_counter == PRESCALER / 2) begin
                data_buf[bit_index] <= rxd;
                bit_index <= bit_index + 1;

                if (bit_index == DATA_WIDTH + 1) begin
                    busy <= 0;
                    bit_index <= 0;
                    

                    if (rxd && ~data_buf[0]) begin
                        data <= data_buf[DATA_WIDTH : 1];
                        ready <= 1;
                    end
                end
            end    
        end
    end

		
endmodule

`default_nettype wire