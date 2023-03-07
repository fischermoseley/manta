`default_nettype none
`timescale 1ns / 1ps

module uart_tx(
	input wire clk,
	
	input wire [7:0] data,
	input wire valid,
	output reg busy,
	output reg ready,

	output reg tx);

	// this transmitter only works with 8N1 serial, at configurable baudrate	
	parameter CLOCKS_PER_BAUD = 868;

	reg [9:0] baud_counter;
	reg [8:0] data_buf;
	reg [3:0] bit_index;

	initial begin
		baud_counter = CLOCKS_PER_BAUD;
		data_buf = 0;
		bit_index = 0;
		busy = 0;
		ready = 1;
		tx = 1;
	end

	always @(posedge clk) begin
		if (valid && !busy) begin
			data_buf <= {1'b1, data};
			bit_index <= 0;
			tx <= 0; //wafflestomp that start bit
			baud_counter <= CLOCKS_PER_BAUD - 1;
			busy <= 1;
			ready <= 0;
		end

		else if (busy) begin
			baud_counter <= baud_counter - 1;

			ready <= (baud_counter == 1) && (bit_index == 9);

			if (baud_counter == 0) begin
				baud_counter <= CLOCKS_PER_BAUD - 1;


				if (bit_index == 9) begin
					if(valid) begin
						data_buf <= {1'b1, data};
						bit_index <= 0;
						tx <= 0;
					end

					else begin
						busy <= 0;
						ready <= 1;
					end
					// if valid happens here then we should bool 
				end

				else begin
					tx <= data_buf[bit_index];
					bit_index <= bit_index + 1;
				end
			end
		end
	end

	

endmodule

`default_nettype wire
