`default_nettype none
`timescale 1ns/1ps

module logic_analyzer_controller (
    input wire clk,

    // from register file
    output reg [3:0] state,
    input wire [15:0] trigger_loc,
    input wire [1:0] trigger_mode,
    input wire request_start,
    input wire request_stop,
    output reg [ADDR_WIDTH-1:0] read_pointer,
    output reg [ADDR_WIDTH-1:0] write_pointer,

    // from trigger block
    input wire trig,

    // block memory user port
    output reg [ADDR_WIDTH-1:0] bram_addr,
    output reg bram_we
    );

    assign bram_addr = write_pointer;

    parameter SAMPLE_DEPTH= 0;
    localparam ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    /* ----- FIFO ----- */
    initial read_pointer = 0;
    initial write_pointer = 0;

    /* ----- FSM ----- */
    localparam IDLE = 0;
    localparam MOVE_TO_POSITION = 1;
    localparam IN_POSITION = 2;
    localparam CAPTURING = 3;
    localparam CAPTURED = 4;

    initial state = IDLE;

    // rising edge detection for start/stop requests
    reg prev_request_start;
    always @(posedge clk) prev_request_start <= request_start;

    reg prev_request_stop;
    always @(posedge clk) prev_request_stop <= request_stop;

    always @(posedge clk) begin
        // don't do anything to the FIFO unless told to

        if(state == IDLE) begin
            write_pointer <= 0;
            read_pointer <= 0;
            bram_we <= 0;

            if(request_start && ~prev_request_start) begin
                state <= MOVE_TO_POSITION;
            end
        end

        else if(state == MOVE_TO_POSITION) begin
            write_pointer <= write_pointer + 1;
            bram_we <= 1;

            if(write_pointer == trigger_loc) begin
                if(trig) state <= CAPTURING;
                else state <= IN_POSITION;
            end
        end

        else if(state == IN_POSITION) begin
            write_pointer <= (write_pointer + 1) % SAMPLE_DEPTH;
            read_pointer <= (read_pointer + 1) % SAMPLE_DEPTH;
            bram_we <= 1;
            if(trig) state <= CAPTURING;
        end

        else if(state == CAPTURING) begin
            if(write_pointer == read_pointer) begin
                bram_we <= 0;
                state <= CAPTURED;
            end

            else write_pointer <= (write_pointer + 1) % SAMPLE_DEPTH;
        end

        if(request_stop && ~prev_request_stop) state <= IDLE;
    end
endmodule

`default_nettype wire