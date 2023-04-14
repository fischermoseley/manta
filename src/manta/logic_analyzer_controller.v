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

    /* ----- FSM ----- */
    localparam IDLE = 0;
    localparam MOVE_TO_POSITION = 1;
    localparam IN_POSITION = 2;
    localparam CAPTURING = 3;
    localparam CAPTURED = 4;

    initial state = IDLE;
    initial current_loc = 0;

    // rising edge detection for start/stop requests
    reg prev_request_start;
    always @(posedge clk) prev_request_start <= request_start;

    reg prev_request_stop;
    always @(posedge clk) prev_request_stop <= request_stop;

    always @(posedge clk) begin
        // don't do anything to the FIFO unless told to
        acquire <= 0;
        pop <= 0;

        if(state == IDLE) begin
            clear <= 1;

            if(request_start && ~prev_request_start) begin
                // TODO: figure out what determines whether or not we
                // go into MOVE_TO_POSITION or IN_POSITION. that's for
                // the morning
                state <= MOVE_TO_POSITION;
            end
        end

        if(state == MOVE_TO_POSITION) begin
            acquire <= 1;
            current_loc <= current_loc + 1;

            if(current_loc == trigger_loc) state <= IN_POSITION
        end

        if(state == IN_POSITION) begin
            acquire <= 1;
            pop <= 1;

            if(trig) pop <= 0;
            if(trig) state <= CAPTURING;
        end

        if(state == CAPTURING) begin
            if(size == DEPTH) state <= CAPTURED;
        end

        if(state == CAPTURED) begin
            // actually nothing to do here doooodeeedoooo
        end

        if(request_stop && ~prev_request_stop) state <= IDLE;

        else state <= IDLE;
    end


    // fifo
    reg acquire;
    reg pop;
    reg [ADDR_WIDTH:0] size,
    reg clear,

	reg [ADDR_WIDTH:0] write_pointer = 0;
    initial read_pointer = 0;
    initial write_pointer = 0;

	assign size = write_pointer - read_pointer;

	always @(posedge clk) begin
        if (clear) read_pointer <= write_pointer;
		if (acquire && size < DEPTH) write_pointer <= write_pointer + 1'd1;
	 	if (pop && size > 0) read_pointer <= read_pointer + 1'd1;
	end
endmodule

`default_nettype wire