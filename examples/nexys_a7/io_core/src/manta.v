`default_nettype none
`timescale 1ns/1ps

/*
This manta definition was generated on 17 Mar 2023 at 20:02:55 by fischerm

If this breaks or if you've got dank formal verification memes,
please contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.
*/

module manta (
    input wire clk,

    input wire rx,
    output reg tx,

    input wire btnu,
    input wire btnd,
    input wire btnl,
    input wire btnr,
    input wire btnc,
    input wire [15:0] sw,
    output reg [15:0] led,
    output reg led16_b,
    output reg led16_g,
    output reg led16_r,
    output reg led17_b,
    output reg led17_g,
    output reg led17_r);

    rx_uart #(.CLOCKS_PER_BAUD(868)) urx (
        .i_clk(clk),
        .i_uart_rx(rx),
        .o_wr(urx_brx_axiv),
        .o_data(urx_brx_axid));

    logic [7:0] urx_brx_axid;
    logic urx_brx_axiv;

    bridge_rx brx (
        .clk(clk),

        .rx_data(urx_brx_axid),
        .rx_valid(urx_brx_axiv),

        .addr_o(brx_my_io_core_addr),
        .wdata_o(brx_my_io_core_wdata),
        .rw_o(brx_my_io_core_rw),
        .valid_o(brx_my_io_core_valid));
        
    reg [15:0] brx_my_io_core_addr;
    reg [15:0] brx_my_io_core_wdata;
    reg brx_my_io_core_rw;
    reg brx_my_io_core_valid;

my_io_core my_io_core_inst(
    .clk(clk),

    // ports
    .btnu(btnu),
    .btnd(btnd),
    .btnl(btnl),
    .btnr(btnr),
    .btnc(btnc),
    .sw(sw),
    .led(led),
    .led16_b(led16_b),
    .led16_g(led16_g),
    .led16_r(led16_r),
    .led17_b(led17_b),
    .led17_g(led17_g),
    .led17_r(led17_r),

    // input port
    .addr_i(brx_my_io_core_addr),
    .wdata_i(brx_my_io_core_wdata),
    .rdata_i(),
    .rw_i(brx_my_io_core_rw),
    .valid_i(brx_my_io_core_valid),

    // output port
    .addr_o(),
    .wdata_o(),
    .rdata_o(my_io_core_btx_rdata),
    .rw_o(my_io_core_btx_rw),
    .valid_o(my_io_core_btx_valid)
    );

    reg [15:0] my_io_core_btx_rdata;
    reg my_io_core_btx_rw;
    reg my_io_core_btx_valid;

    bridge_tx btx (
        .clk(clk),

        .rdata_i(my_io_core_btx_rdata),
        .rw_i(my_io_core_btx_rw),
        .valid_i(my_io_core_btx_valid),

        .ready_i(utx_btx_ready),
        .data_o(btx_utx_data),
        .valid_o(btx_utx_valid));

    logic utx_btx_ready;
    logic btx_utx_valid;
    logic [7:0] btx_utx_data;

    uart_tx #(.CLOCKS_PER_BAUD(868)) utx (
        .clk(clk),

        .data(btx_utx_data),
        .valid(btx_utx_valid),
        .ready(utx_btx_ready),

        .tx(tx));
endmodule

 /* ---- Module Definitions ----  */
////////////////////////////////////////////////////////////////////////////////
//
// Filename: 	rxuart.v
//
// Project:	Verilog Tutorial Example file
//
// Purpose:	Receives a character from a UART (serial port) wire.  Key
//		features of this core include:
//
//	- The baud rate is constant, and set by the CLOCKS_PER_BAUD parameter.
//		To be successful, one baud interval must be (approximately)
//		equal to CLOCKS_PER_BAUD / CLOCK_RATE_HZ seconds long.
//
//	- The protocol used is the basic 8N1: 8 data bits, 1 stop bit, and no
//		parity.
//
//	- This core has no reset
//	- This core has no error detection for frame errors
//	- This core cannot detect, report, or even recover from, a break
//		condition on the line.  A break condition is defined as a
//		period of time where the i_uart_rx line is held low for longer
//		than one data byte (10 baud intervals)
//
//	- There's no clock rate detection in this core
//
//	Perhaps one of the nicer features of this core is that it (can be)
//	formally verified.  It depends upon a separate (formally verified)
//	transmit core for this purpose.
//
//	As with the other cores within this tutorial, there may (or may not) be
//	bugs within this design for you to find.
//
//
// Creator:	Dan Gisselquist, Ph.D.
//		Gisselquist Technology, LLC
//
////////////////////////////////////////////////////////////////////////////////
//
// Written and distributed by Gisselquist Technology, LLC
//
// This program is hereby granted to the public domain.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY or
// FITNESS FOR A PARTICULAR PURPOSE.
//
////////////////////////////////////////////////////////////////////////////////
//
//


module rx_uart(
	input wire i_clk,
	input wire i_uart_rx,
	output reg o_wr,
	output reg [7:0] o_data);

	parameter  [15:0]	CLOCKS_PER_BAUD = 868;
	localparam	[3:0]	IDLE      = 4'h0;
	localparam	[3:0]	BIT_ZERO  = 4'h1;
	// localparam	[3:0]	BIT_ONE   = 4'h2;
	// localparam	[3:0]	BIT_TWO   = 4'h3;
	// localparam	[3:0]	BIT_THREE = 4'h4;
	// localparam	[3:0]	BIT_FOUR  = 4'h5;
	// localparam	[3:0]	BIT_FIVE  = 4'h6;
	// localparam	[3:0]	BIT_SIX   = 4'h7;
	// localparam	[3:0]	BIT_SEVEN = 4'h8;
	localparam	[3:0]	STOP_BIT  = 4'h9;

	reg	[3:0]		state;
	reg	[15:0]		baud_counter;
	reg			zero_baud_counter;

	// 2FF Synchronizer
	//
	reg		ck_uart;
	reg		q_uart;
	initial	{ ck_uart, q_uart } = -1;
	always @(posedge i_clk)
		{ ck_uart, q_uart } <= { q_uart, i_uart_rx };

	initial	state = IDLE;
	initial	baud_counter = 0;

	always @(posedge i_clk)
		if (state == IDLE) begin
			state <= IDLE;
			baud_counter <= 0;
			if (!ck_uart) begin
				state <= BIT_ZERO;
				baud_counter <= CLOCKS_PER_BAUD+CLOCKS_PER_BAUD/2-1'b1;
			end
		end

		else if (zero_baud_counter) begin
			state <= state + 1;
			baud_counter <= CLOCKS_PER_BAUD-1'b1;
			if (state == STOP_BIT) begin
				state <= IDLE;
				baud_counter <= 0;
			end
		end 

		else baud_counter <= baud_counter - 1'b1;

	always @(*)
		zero_baud_counter = (baud_counter == 0);

	always @(posedge i_clk)
	if ((zero_baud_counter)&&(state != STOP_BIT))
		o_data <= { ck_uart, o_data[7:1] };

	initial	o_wr = 1'b0;
	always @(posedge i_clk)
		o_wr <= ((zero_baud_counter)&&(state == STOP_BIT));

endmodule




module bridge_rx(
    input wire clk,

    input wire[7:0] rx_data,
    input wire rx_valid,

    output reg[15:0] addr_o,
    output reg[15:0] wdata_o,
    output reg rw_o,
    output reg valid_o
);


// this is a hack, the FSM needs to be updated
// but this will bypass it for now
parameter ready_i = 1;

parameter ADDR_WIDTH = 0;
parameter DATA_WIDTH = 0;

localparam PREAMBLE = 8'h4D;
localparam CR = 8'h0D;
localparam LF = 8'h0A;

localparam ACQUIRE = 0;
localparam TRANSMIT = 1;
localparam ERROR = 2;

reg [1:0] state;
reg [3:0] bytes_received;

// no global resets!
initial begin
    addr_o = 0;
    wdata_o = 0;
    rw_o = 0;
    valid_o = 0;
    bytes_received = 0;
    state = ACQUIRE;
end

reg [3:0] rx_data_decoded;
reg rx_data_is_0_thru_9;
reg rx_data_is_A_thru_F;

always @(*) begin
    rx_data_is_0_thru_9 = (rx_data >= 8'h30) & (rx_data <= 8'h39);
    rx_data_is_A_thru_F = (rx_data >= 8'h41) & (rx_data <= 8'h46);

    if (rx_data_is_0_thru_9) rx_data_decoded = rx_data - 8'h30;
    else if (rx_data_is_A_thru_F) rx_data_decoded = rx_data - 8'h41 + 'd10;
    else rx_data_decoded = 0;
end


always @(posedge clk) begin
    if (state == ACQUIRE) begin
        if(rx_valid) begin

            if (bytes_received == 0) begin
                if(rx_data == PREAMBLE) bytes_received <= 1;
            end

            else if( (bytes_received >= 1) & (bytes_received <= 4) ) begin
                // only advance if byte is valid hex digit
                if(rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                    addr_o <= (addr_o << 4) | rx_data_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if( bytes_received == 5) begin
                    if( (rx_data == CR) | (rx_data == LF)) begin
                        valid_o <= 1;
                        rw_o = 0;
                        bytes_received <= 0;
                        state <= TRANSMIT;
                    end

                    else if (rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                        bytes_received <= bytes_received + 1;
                        wdata_o <= (wdata_o << 4) | rx_data_decoded;
                    end

                    else state <= ERROR;
            end

            else if ( (bytes_received >= 6) & (bytes_received <= 8) ) begin

                if (rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                    wdata_o <= (wdata_o << 4) | rx_data_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if (bytes_received == 9) begin
                bytes_received <= 0;
                if( (rx_data == CR) | (rx_data == LF)) begin
                    valid_o <= 1;
                    rw_o <= 1;
                    state <= TRANSMIT;
                end

                else state <= ERROR;
            end
        end
    end


    else if (state == TRANSMIT) begin
        if(ready_i) begin
            valid_o <= 0;
            state <= ACQUIRE;
        end

        if(rx_valid) begin
            if ( (rx_data != CR) & (rx_data != LF)) begin
                valid_o <= 0;
                state <= ERROR;
            end
        end
    end
end

endmodule


module my_io_core (
    input wire clk,

    // ports
    input wire btnu,
    input wire btnd,
    input wire btnl,
    input wire btnr,
    input wire btnc,
    input wire [15:0] sw,
    output reg [15:0] led,
    output reg led16_b,
    output reg led16_g,
    output reg led16_r,
    output reg led17_b,
    output reg led17_g,
    output reg led17_r,

    // input port
    input wire [15:0] addr_i,
    input wire [15:0] wdata_i,
    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i,

    // output port
    output reg [15:0] addr_o,
    output reg [15:0] wdata_o,
    output reg [15:0] rdata_o,
    output reg rw_o,
    output reg valid_o
    );

parameter BASE_ADDR = 0;
always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;


        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 12)) begin

            if(!rw_i) begin // reads
                case (addr_i)
					0: rdata_o <= {15'b0, btnu};
					1: rdata_o <= {15'b0, btnd};
					2: rdata_o <= {15'b0, btnl};
					3: rdata_o <= {15'b0, btnr};
					4: rdata_o <= {15'b0, btnc};
					5: rdata_o <= sw;
					6: rdata_o <= led;
					7: rdata_o <= {15'b0, led16_b};
					8: rdata_o <= {15'b0, led16_g};
					9: rdata_o <= {15'b0, led16_r};
					10: rdata_o <= {15'b0, led17_b};
					11: rdata_o <= {15'b0, led17_g};
					12: rdata_o <= {15'b0, led17_r};
                endcase
            end

            else begin // writes
                case (addr_i)
					6: led <= wdata_i;
					7: led16_b <= wdata_i[0];
					8: led16_g <= wdata_i[0];
					9: led16_r <= wdata_i[0];
					10: led17_b <= wdata_i[0];
					11: led17_g <= wdata_i[0];
					12: led17_r <= wdata_i[0];
                endcase
            end
        end
    end
endmodule



module bridge_tx(
    input wire clk,

    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i,

    output reg [7:0] data_o,
    input wire ready_i,
    output reg valid_o);

localparam PREAMBLE = 8'h4D;
localparam CR = 8'h0D;
localparam LF = 8'h0A;

logic busy;
logic [15:0] buffer;
logic [3:0] byte_counter;

initial begin
    busy = 0;
    buffer = 0;
    byte_counter = 0; 
    valid_o = 0;
end

always @(posedge clk) begin
    if (!busy) begin
        if (valid_i && !rw_i) begin
            busy <= 1;
            buffer <= rdata_i;
            byte_counter <= 0;
            valid_o <= 1;
        end
    end

    if (busy) begin

        if(ready_i) begin
            byte_counter <= byte_counter + 1;
            
            if (byte_counter > 5) begin
                byte_counter <= 0;

                // stop transmitting if we don't have both valid and read
                if ( !(valid_i && !rw_i) ) begin
                    busy <= 0;
                    valid_o <= 0;
                end
            end
        end
    end
end

always @(*) begin
    case (byte_counter)
        0: data_o = PREAMBLE;
        1: data_o = (buffer[15:12] < 10) ? (buffer[15:12] + 8'h30) : (buffer[15:12] + 8'h41 - 'd10);
        2: data_o = (buffer[11:8] < 10) ? (buffer[11:8] + 8'h30) : (buffer[11:8] + 8'h41 - 'd10); 
        3: data_o = (buffer[7:4] < 10) ? (buffer[7:4] + 8'h30) : (buffer[7:4] + 8'h41 - 'd10);
        4: data_o = (buffer[3:0] < 10) ? (buffer[3:0] + 8'h30) : (buffer[3:0] + 8'h41 - 'd10);
        5: data_o = CR;
        6: data_o = LF;
        default: data_o = 0;
    endcase
end

endmodule




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