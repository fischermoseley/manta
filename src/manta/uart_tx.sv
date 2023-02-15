`default_nettype none
`timescale 1ns / 1ps


module uart_tx(
	input wire clk,
	input wire rst,
	input wire [DATA_WIDTH-1:0] data,
	input wire start,
	
	output logic busy,
	output logic txd
	);

	// Just going to stick to 8N1 for now, we'll come back and
	// parameterize this later.
	
	parameter DATA_WIDTH = 8;
	parameter CLK_FREQ_HZ = 100_000_000;
	parameter BAUDRATE = 115200;

	localparam PRESCALER = CLK_FREQ_HZ / BAUDRATE;

	logic [$clog2(PRESCALER) - 1:0] baud_counter;
	logic [$clog2(DATA_WIDTH + 2):0] bit_index;
	logic [DATA_WIDTH - 1:0] data_buf;

	// make secondary logic for baudrate
	always_ff @(posedge clk) begin
		if(rst) baud_counter <= 0;
		else begin
			baud_counter <= (baud_counter == PRESCALER - 1) ? 0 : baud_counter + 1;
		end
	end
	
	always_ff @(posedge clk) begin
		
		// reset logic
		if(rst) begin
			bit_index <= 0;
			busy <= 0;
			txd <= 1; // idle high
		end

		// enter transmitting state logic
		// don't allow new requests to interrupt current
		// transfers
		if(start && ~busy) begin
			busy <= 1;
			data_buf <= data;
		end


		// transmitting state logic
		else if(baud_counter == 0 && busy) begin

			if (bit_index == 0) begin
				txd <= 0;
				bit_index <= bit_index + 1;
			end

			else if ((bit_index < DATA_WIDTH + 1) && (bit_index > 0)) begin
				txd <= data_buf[bit_index - 1];
				bit_index <= bit_index + 1;
			end
			
			else if (bit_index == DATA_WIDTH + 1) begin
				txd <= 1;
				bit_index <= bit_index + 1;
			end

			else if (bit_index >= DATA_WIDTH + 1) begin
				busy <= 0;
				bit_index <= 0;
			end
		end
	end
endmodule


`default_nettype wire
