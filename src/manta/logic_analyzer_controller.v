`default_nettype none
`timescale 1ns/1ps

module logic_analyzer_controller (
    input wire clk,

    // from register file
    output reg [3:0] state,
    input wire signed [15:0] trigger_loc,
    output reg signed [15:0] current_loc,
    input wire request_start,
    input wire request_stop,
    output reg read_pointer,

    // from trigger block
    input wire trig,

    // block memory user port
    output [ADDR_WIDTH-1:0] bram_addr,
    output bram_we
    );

    parameter DEPTH = 0;
    localparam ADDR_WIDTH = $clog2(DEPTH);

    // fsm
    localparam IDLE = 0;
    localparam START_CAPTURE = 1;
    localparam MOVE_TO_POSITION = 2;
    localparam IN_POSITION = 3;
    localparam FILLING_BUFFER = 4;
    localparam FILLED = 5;

    initial state = IDLE;
    initial current_loc = 0;
    initial read_pointer = 0;
    initial write_pointer = 0;

    always @(posedge clk) begin
        if(state == IDLE) begin
            current_loc <= (trigger_loc < 0) ? trigger_loc : 0;
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
                current_loc <= current_loc + 1;
                // add code to add samples to word FIFO
                fifo_acquire <= 1;
                if (current_loc == trigger_loc) state <= IN_POSITION;
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

            current_loc <= (trigger_loc < 0) ? trigger_loc : 0;
        end


        // return to IDLE state if somehow we get to a state that doesn't exist
        else begin
            state <= IDLE;
        end
    end


    // fifo
    reg acquire;
    reg pop;
    reg [ADDR_WIDTH:0] size,
    reg clear,

	reg [ADDR_WIDTH:0] write_pointer = 0;
	reg [ADDR_WIDTH:0] read_pointer = 0;

	assign size = write_pointer - read_pointer;

	always @(posedge clk) begin
        if (clear) read_pointer <= write_pointer;
		if (acquire && size < DEPTH) write_pointer <= write_pointer + 1'd1;
	 	if (pop && size > 0) read_pointer <= read_pointer + 1'd1;
	end
endmodule

`default_nettype wire