`default_nettype none
`timescale 1ns / 1ps

module uart_tx(
	input wire clk,
	input wire rst,
	
	input wire [DATA_WIDTH-1:0] axiid,
	input wire axiiv,
	output reg axiir,

	output reg txd
	);
	
	parameter DATA_WIDTH = 0;
	parameter CLK_FREQ_HZ = 0;
	parameter BAUDRATE = 0;

	localparam BAUD_PERIOD = CLK_FREQ_HZ / BAUDRATE;

	reg busy;
	assign axiir = ~busy; 

	reg [$clog2(BAUD_PERIOD) - 1:0] baud_counter;
	reg [$clog2(DATA_WIDTH + 2):0] bit_index;
	reg [DATA_WIDTH - 1:0] data_buf;

	// make secondary logic for baudrate
	always @(posedge clk) begin
		if(rst) baud_counter <= 0;
		else begin
			baud_counter <= (baud_counter == BAUD_PERIOD - 1) ? 0 : baud_counter + 1;
		end
	end
	
	always @(posedge clk) begin
		
		// reset logic
		if(rst) begin
			bit_index <= 0;
			busy <= 0;
			txd <= 1; // idle high
		end

		// enter transmitting state logic
		// don't allow new requests to interrupt current
		// transfers
		if(axiiv && ~busy) begin
			busy <= 1;
			baud_counter <= 0;
			data_buf <= axiid;
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
