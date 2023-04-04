`default_nettype none
`timescale 1ns/1ps

/*
This manta definition was generated on 03 Apr 2023 at 21:11:41 by fischerm

If this breaks or if you've got dank formal verification memes,
please contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured,
feel free to copy-paste this into your source!

manta manta_inst (
    .clk(clk),

    .rx(rx),
    .tx(tx),

    .larry(larry),
    .curly(curly),
    .moe(moe),
    .shemp(shemp));

*/

module manta (
    input wire clk,

    input wire rx,
    output reg tx,

    input wire larry,
    input wire curly,
    input wire moe,
    input wire [3:0] shemp);

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

        .addr_o(brx_my_logic_analyzer_addr),
        .wdata_o(brx_my_logic_analyzer_wdata),
        .rw_o(brx_my_logic_analyzer_rw),
        .valid_o(brx_my_logic_analyzer_valid));

    reg [15:0] brx_my_logic_analyzer_addr;
    reg [15:0] brx_my_logic_analyzer_wdata;
    reg brx_my_logic_analyzer_rw;
    reg brx_my_logic_analyzer_valid;

    logic_analyzer #(.BASE_ADDR(0), .SAMPLE_DEPTH(128)) my_logic_analyzer (
        .clk(clk),

        .addr_i(brx_my_logic_analyzer_addr),
        .wdata_i(brx_my_logic_analyzer_wdata),
        .rdata_i(),
        .rw_i(brx_my_logic_analyzer_rw),
        .valid_i(brx_my_logic_analyzer_valid),

        .larry(larry),
		.curly(curly),
		.moe(moe),
		.shemp(shemp),

        .addr_o(),
        .wdata_o(),
        .rdata_o(my_logic_analyzer_btx_rdata),
        .rw_o(my_logic_analyzer_btx_rw),
        .valid_o(my_logic_analyzer_btx_valid));

    reg [15:0] my_logic_analyzer_btx_rdata;
    reg my_logic_analyzer_btx_rw;
    reg my_logic_analyzer_btx_valid;

    bridge_tx btx (
        .clk(clk),

        .rdata_i(my_logic_analyzer_btx_rdata),
        .rw_i(my_logic_analyzer_btx_rw),
        .valid_i(my_logic_analyzer_btx_valid),

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




module logic_analyzer(
    input wire clk,

    // probes
    input wire larry,
    input wire curly,
    input wire moe,
    input wire [3:0] shemp,

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
    parameter SAMPLE_DEPTH = 0;

    // fsm
    la_fsm #(.BASE_ADDR(BASE_ADDR), .SAMPLE_DEPTH(SAMPLE_DEPTH)) fsm (
        .clk(clk),

        .trig(trig),
        .fifo_size(fifo_size),
        .fifo_acquire(fifo_acquire),
        .fifo_pop(fifo_pop),
        .fifo_clear(fifo_clear),

        .addr_i(addr_i),
        .wdata_i(wdata_i),
        .rdata_i(rdata_i),
        .rw_i(rw_i),
        .valid_i(valid_i),

        .addr_o(fsm_trig_blk_addr),
        .wdata_o(fsm_trig_blk_wdata),
        .rdata_o(fsm_trig_blk_rdata),
        .rw_o(fsm_trig_blk_rw),
        .valid_o(fsm_trig_blk_valid));

    reg [15:0] fsm_trig_blk_addr;
    reg [15:0] fsm_trig_blk_wdata;
    reg [15:0] fsm_trig_blk_rdata;
    reg fsm_trig_blk_rw;
    reg fsm_trig_blk_valid;

    reg trig;
    reg [$clog2(SAMPLE_DEPTH):0] fifo_size;
    reg fifo_acquire;
    reg fifo_pop;
    reg fifo_clear;


    // trigger block
    trigger_block #(.BASE_ADDR(BASE_ADDR + 3)) trig_blk(
        .clk(clk),

        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp),

        .trig(trig),

        .addr_i(fsm_trig_blk_addr),
        .wdata_i(fsm_trig_blk_wdata),
        .rdata_i(fsm_trig_blk_rdata),
        .rw_i(fsm_trig_blk_rw),
        .valid_i(fsm_trig_blk_valid),

        .addr_o(trig_blk_sample_mem_addr),
        .wdata_o(trig_blk_sample_mem_wdata),
        .rdata_o(trig_blk_sample_mem_rdata),
        .rw_o(trig_blk_sample_mem_rw),
        .valid_o(trig_blk_sample_mem_valid));

    reg [15:0] trig_blk_sample_mem_addr;
    reg [15:0] trig_blk_sample_mem_wdata;
    reg [15:0] trig_blk_sample_mem_rdata;
    reg trig_blk_sample_mem_rw;
    reg trig_blk_sample_mem_valid;

    // sample memory
    sample_mem #(.BASE_ADDR(BASE_ADDR + 11), .SAMPLE_DEPTH(SAMPLE_DEPTH)) sample_mem(
        .clk(clk),

        // fifo
        .acquire(fifo_acquire),
        .pop(fifo_pop),
        .size(fifo_size),
        .clear(fifo_clear),

        // probes
        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp),

        // input port
        .addr_i(trig_blk_sample_mem_addr),
        .wdata_i(trig_blk_sample_mem_wdata),
        .rdata_i(trig_blk_sample_mem_rdata),
        .rw_i(trig_blk_sample_mem_rw),
        .valid_i(trig_blk_sample_mem_valid),

        // output port
        .addr_o(addr_o),
        .wdata_o(wdata_o),
        .rdata_o(rdata_o),
        .rw_o(rw_o),
        .valid_o(valid_o));
endmodule




module la_fsm(
    input wire clk,

    input wire trig,
    input wire [$clog2(SAMPLE_DEPTH):0] fifo_size,
    output reg fifo_acquire,
    output reg fifo_pop,
    output reg fifo_clear,

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
    output reg valid_o);

    parameter BASE_ADDR = 0;
    parameter SAMPLE_DEPTH = 0;

    // state machine
    localparam IDLE = 0;
    localparam START_CAPTURE = 1;
    localparam MOVE_TO_POSITION = 2;
    localparam IN_POSITION = 3;
    localparam FILLING_BUFFER = 4;
    localparam FILLED = 5;

    reg [3:0] state;
    reg signed [15:0] trigger_loc;
    reg signed [15:0] present_loc;

    initial state = IDLE;
    initial trigger_loc = 0;
    initial present_loc = 0;

    // perform register operations
    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;

        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 2)) begin

            if(!rw_i) begin // reads
                case (addr_i)
                    BASE_ADDR + 0: rdata_o <= state;
                    BASE_ADDR + 1: rdata_o <= trigger_loc;
                    BASE_ADDR + 2: rdata_o <= present_loc;
                endcase
            end

            else begin // writes
                case (addr_i)
                    BASE_ADDR + 0: state <= wdata_i;
                    BASE_ADDR + 1: trigger_loc <= wdata_i;
                    //BASE_ADDR + 2: present_loc <= wdata_i;
                endcase
            end
        end
//    end

    // run state machine
//    always @(posedge clk) begin
        if(state == IDLE) begin
            present_loc <= (trigger_loc < 0) ? trigger_loc : 0;
        end

        else if(state == START_CAPTURE) begin
            // perform whatever setup is needed before starting the next capture
            fifo_clear <= 1;
            state <= MOVE_TO_POSITION;
        end

        else if(state == MOVE_TO_POSITION) begin
            fifo_clear <= 0;
            // if trigger location is negative or zero,
            // then we're already in position
            if(trigger_loc <= 0) state <= IN_POSITION;

            // otherwise we'll need to wait a little,
            // but we'll need to buffer along the way
            else begin
                present_loc <= present_loc + 1;
                // add code to add samples to word FIFO
                fifo_acquire <= 1;
                if (present_loc == trigger_loc) state <= IN_POSITION;
            end
        end

        else if(state == IN_POSITION) begin
            // pop stuff out of the word FIFO in addition to pulling it in
            fifo_acquire <= 1;
            fifo_pop <= 1;

            if(trig) state <= FILLING_BUFFER;
        end

        else if(state == FILLING_BUFFER) begin
            fifo_acquire <= 1;
            fifo_pop <= 0;
            if(fifo_size == SAMPLE_DEPTH) state <= FILLED;
        end

        else if(state == FILLED) begin
            // don't automatically go back to IDLE, the host will move
            // the state to MOVE_TO_POSITION

            present_loc <= (trigger_loc < 0) ? trigger_loc : 0;
        end


        // return to IDLE state if somehow we get to a state that doesn't exist
        else begin
            state <= IDLE;
        end
    end
endmodule




module sample_mem(
    input wire clk,

    // fifo
    input wire acquire,
    input wire pop,
    output logic [BRAM_ADDR_WIDTH:0] size,
    input wire clear,

    // probes
    input wire larry,
    input wire curly,
    input wire moe,
    input wire [3:0] shemp,

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
    output reg valid_o);

    parameter BASE_ADDR = 0;
    parameter SAMPLE_DEPTH = 0;
    localparam BRAM_ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    // bus controller
    reg [BRAM_ADDR_WIDTH-1:0] bram_read_addr;
    reg [15:0] bram_read_data;

    always @(*) begin
        // if address is valid
        if ( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + SAMPLE_DEPTH) ) begin

            // figure out proper place to read from
            // want to read from the read pointer, and then loop back around
            if(read_pointer + (addr_i - BASE_ADDR) > SAMPLE_DEPTH)
                bram_read_addr = read_pointer + (addr_i - BASE_ADDR) - SAMPLE_DEPTH;

            else
                bram_read_addr = read_pointer + (addr_i - BASE_ADDR);
        end

        else bram_read_addr = 0;
    end


    // pipeline bus to compensate for 2-cycles of delay in BRAM
    reg [15:0] addr_pip;
    reg [15:0] wdata_pip;
    reg [15:0] rdata_pip;
    reg rw_pip;
    reg valid_pip;

    always @(posedge clk) begin
        addr_pip <= addr_i;
        wdata_pip <= wdata_i;
        rdata_pip <= rdata_i;
        rw_pip <= rw_i;
        valid_pip <= valid_i;

        addr_o <= addr_pip;
        wdata_o <= wdata_pip;
        rdata_o <= rdata_pip;
        rw_o <= rw_pip;
        valid_o <= valid_pip;

        if( valid_pip && !rw_pip && (addr_pip >= BASE_ADDR) && (addr_pip <= BASE_ADDR + SAMPLE_DEPTH) )
            rdata_o <= bram_read_data;
    end


    // bram
    dual_port_bram #(
		.RAM_WIDTH(16),
		.RAM_DEPTH(SAMPLE_DEPTH)
    ) bram (
		// read port (controlled by bus)
		.clka(clk),
		.addra(bram_read_addr),
		.dina(16'b0),
		.wea(1'b0),
		.douta(bram_read_data),

		// write port (controlled by FIFO)
		.clkb(clk),
		.addrb(write_pointer[BRAM_ADDR_WIDTH-1:0]),
		.dinb({9'b0, larry, curly, moe, shemp}),
		.web(acquire),
		.doutb());


    // fifo
	reg [BRAM_ADDR_WIDTH:0] write_pointer = 0;
	reg [BRAM_ADDR_WIDTH:0] read_pointer = 0;

	assign size = write_pointer - read_pointer;

	always @(posedge clk) begin
        if (clear) read_pointer <= write_pointer;
		if (acquire && size < SAMPLE_DEPTH) write_pointer <= write_pointer + 1'd1;
	 	if (pop && size > 0) read_pointer <= read_pointer + 1'd1;
	end
endmodule


//  Xilinx True Dual Port RAM, Read First, Dual Clock
//  This code implements a parameterizable true dual port memory (both ports can read and write).
//  The behavior of this RAM is when data is written, the prior memory contents at the write
//  address are presented on the output port.  If the output data is
//  not needed during writes or the last read value is desired to be retained,
//  it is suggested to use a no change RAM as it is more power efficient.
//  If a reset or enable is not necessary, it may be tied off or removed from the code.

//  Modified from the xilinx_true_dual_port_read_first_2_clock_ram verilog language template.

module dual_port_bram #(
    parameter RAM_WIDTH = 0,                        // Specify RAM data width
    parameter RAM_DEPTH = 0                         // Specify RAM depth (number of entries)
    ) (
    input wire [$clog2(RAM_DEPTH-1)-1:0] addra,  // Port A address bus, width determined from RAM_DEPTH
    input wire [$clog2(RAM_DEPTH-1)-1:0] addrb,  // Port B address bus, width determined from RAM_DEPTH
    input wire [RAM_WIDTH-1:0] dina,           // Port A RAM input data
    input wire [RAM_WIDTH-1:0] dinb,           // Port B RAM input data
    input wire clka,                           // Port A clock
    input wire clkb,                           // Port B clock
    input wire wea,                            // Port A write enable
    input wire web,                            // Port B write enable
    output wire [RAM_WIDTH-1:0] douta,         // Port A RAM output data
    output wire [RAM_WIDTH-1:0] doutb          // Port B RAM output data
    );

    reg [RAM_WIDTH-1:0] BRAM [RAM_DEPTH-1:0];
    reg [RAM_WIDTH-1:0] ram_data_a = {RAM_WIDTH{1'b0}};
    reg [RAM_WIDTH-1:0] ram_data_b = {RAM_WIDTH{1'b0}};

    always @(posedge clka) begin
        if (wea) BRAM[addra] <= dina;
        ram_data_a <= BRAM[addra];
    end

    always @(posedge clkb) begin
        if (web) BRAM[addrb] <= dinb;
        ram_data_b <= BRAM[addrb];
    end

    // The following is a 2 clock cycle read latency with improve clock-to-out timing
    reg [RAM_WIDTH-1:0] douta_reg = {RAM_WIDTH{1'b0}};
    reg [RAM_WIDTH-1:0] doutb_reg = {RAM_WIDTH{1'b0}};

    always @(posedge clka) douta_reg <= ram_data_a;
    always @(posedge clkb) doutb_reg <= ram_data_b;

    assign douta = douta_reg;
    assign doutb = doutb_reg;
endmodule



module trigger_block (
    input wire clk,

    // probes
    input wire larry,
	input wire curly,
	input wire moe,
	input wire [3:0] shemp,

    // trigger
    output reg trig,

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
    output reg valid_o);

    parameter BASE_ADDR = 0;
    localparam MAX_ADDR = 7;

    // trigger configuration registers
    // - each probe gets an operation and a compare register
    // - at the end we OR them all together. along with any custom probes the user specs

    reg [3:0] larry_trigger_op = 0;
	reg larry_trigger_arg = 0;
	reg larry_trig;

    trigger #(.INPUT_WIDTH(1)) larry_trigger (
        .clk(clk),

        .probe(larry),
        .op(larry_trigger_op),
        .arg(larry_trigger_arg),
        .trig(larry_trig)
    );
    reg [3:0] curly_trigger_op = 0;
	reg curly_trigger_arg = 0;
	reg curly_trig;

    trigger #(.INPUT_WIDTH(1)) curly_trigger (
        .clk(clk),

        .probe(curly),
        .op(curly_trigger_op),
        .arg(curly_trigger_arg),
        .trig(curly_trig)
    );
    reg [3:0] moe_trigger_op = 0;
	reg moe_trigger_arg = 0;
	reg moe_trig;

    trigger #(.INPUT_WIDTH(1)) moe_trigger (
        .clk(clk),

        .probe(moe),
        .op(moe_trigger_op),
        .arg(moe_trigger_arg),
        .trig(moe_trig)
    );
    reg [3:0] shemp_trigger_op = 0;
	reg [3:0] shemp_trigger_arg = 0;
	reg shemp_trig;

    trigger #(.INPUT_WIDTH(4)) shemp_trigger (
        .clk(clk),

        .probe(shemp),
        .op(shemp_trigger_op),
        .arg(shemp_trigger_arg),
        .trig(shemp_trig)
    );

    assign trig = larry_trig || curly_trig || moe_trig || shemp_trig;

    // perform register operations
    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;

        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + MAX_ADDR) ) begin

            // reads
            if(valid_i && !rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: rdata_o <= larry_trigger_op;
					BASE_ADDR + 1: rdata_o <= larry_trigger_arg;
					BASE_ADDR + 2: rdata_o <= curly_trigger_op;
					BASE_ADDR + 3: rdata_o <= curly_trigger_arg;
					BASE_ADDR + 4: rdata_o <= moe_trigger_op;
					BASE_ADDR + 5: rdata_o <= moe_trigger_arg;
					BASE_ADDR + 6: rdata_o <= shemp_trigger_op;
					BASE_ADDR + 7: rdata_o <= shemp_trigger_arg;
                endcase
            end

            // writes
            else if(valid_i && rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: larry_trigger_op <= wdata_i;
					BASE_ADDR + 1: larry_trigger_arg <= wdata_i;
					BASE_ADDR + 2: curly_trigger_op <= wdata_i;
					BASE_ADDR + 3: curly_trigger_arg <= wdata_i;
					BASE_ADDR + 4: moe_trigger_op <= wdata_i;
					BASE_ADDR + 5: moe_trigger_arg <= wdata_i;
					BASE_ADDR + 6: shemp_trigger_op <= wdata_i;
					BASE_ADDR + 7: shemp_trigger_arg <= wdata_i;
                endcase
            end
        end
    end
endmodule




module trigger(
    input wire clk,

    input wire [INPUT_WIDTH-1:0] probe,
    input wire [3:0] op,
    input wire [INPUT_WIDTH-1:0] arg,

    output reg trig
    );

    parameter INPUT_WIDTH = 0;

    localparam DISABLE = 0;
    localparam RISING = 1;
    localparam FALLING = 2;
    localparam CHANGING = 3;
    localparam GT = 4;
    localparam LT = 5;
    localparam GEQ = 6;
    localparam LEQ = 7;
    localparam EQ = 8;
    localparam NEQ = 9;

    reg [INPUT_WIDTH-1:0] probe_prev = 0;
    always @(posedge clk) probe_prev <= probe;

    always @(*) begin
        case (op)
            RISING :    trig = (probe > probe_prev);
            FALLING :   trig = (probe < probe_prev);
            CHANGING :  trig = (probe != probe_prev);
            GT:         trig = (probe > arg);
            LT:         trig = (probe < arg);
            GEQ:        trig = (probe >= arg);
            LEQ:        trig = (probe <= arg);
            EQ:         trig = (probe == arg);
            NEQ:        trig = (probe != arg);
            default:    trig = 0;
        endcase
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