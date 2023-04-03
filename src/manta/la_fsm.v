`default_nettype none
`timescale 1ns/1ps

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

`default_nettype wire