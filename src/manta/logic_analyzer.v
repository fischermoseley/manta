`default_nettype none
`timescale 1ns/1ps

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
    parameter SAMPLE_DEPTH = 4096;

    // trigger configuration registers
    // - each probe gets an operation and a compare register
    // - at the end we AND them all together. along with any custom probes the user specs

    reg [3:0] larry_trigger_op;
    reg larry_trigger_arg;
    reg larry_trig;
    trigger #(.INPUT_WIDTH(1)) larry_trigger(
        .clk(clk),

        .probe(larry),
        .op(larry_trigger_op),
        .arg(larry_trigger_arg),
        .trig(larry_trig));

    reg [3:0] curly_trigger_op;
    reg curly_trigger_arg;
    reg curly_trig;
    trigger #(.INPUT_WIDTH(1)) curly_trigger(
        .clk(clk),

        .probe(curly),
        .op(curly_trigger_op),
        .arg(curly_trigger_arg),
        .trig(curly_trig));


    reg [3:0] moe_trigger_op;
    reg moe_trigger_arg;
    reg moe_trig;
    trigger #(.INPUT_WIDTH(1)) moe_trigger(
        .clk(clk),

        .probe(moe),
        .op(moe_trigger_op),
        .arg(moe_trigger_arg),
        .trig(moe_trig));

    reg [3:0] shemp_trigger_op;
    reg [3:0] shemp_trigger_arg;
    reg shemp_trig;
    trigger #(.INPUT_WIDTH(4)) shemp_trigger(
        .clk(clk),

        .probe(shemp),
        .op(shemp_trigger_op),
        .arg(shemp_trigger_arg),
        .trig(shemp_trig));

    reg triggered;
    assign triggered = larry_trig || curly_trig || moe_trig || shemp_trig;

    reg [6:0] concatenated;
    assign concatenated = {larry, curly, moe, shemp};
    
    // word-wise fifo 
    fifo #(.WIDTH(FIFO_WIDTH), .DEPTH(SAMPLE_DEPTH)) wfifo(
        .clk(clk),
        .bram_rst(1'b0),

        .in(concatenated),
        .in_valid(wfifo_in_valid),

        .out(wfifo_out),
        .out_req(wfifo_out_req),
        .out_valid(wfifo_out_valid),
        
        .size(wfifo_size),
        .empty(),
        .full());

    reg wfifo_in_valid;
    localparam FIFO_WIDTH = 7;
    reg [FIFO_WIDTH-1:0] wfifo_out;
    reg wfifo_out_req;
    reg wfifo_out_valid;

    reg [$clog2(SAMPLE_DEPTH):0] wfifo_size;

    
    // state machine 
    localparam IDLE = 0;
    localparam START = 1;
    localparam MOVE_TO_POSITION = 2;
    localparam IN_POSITION = 3;
    localparam FILLING_BUFFER = 4;
    localparam FILLED = 5;

    reg [3:0] state;
    initial state = IDLE;

    reg signed [15:0] trigger_loc;
    initial trigger_loc = 0;

    reg signed [15:0] present_loc;
    initial present_loc = 0;

    always @(posedge clk) begin
        if(state == IDLE) begin
            present_loc <= (trigger_loc < 0) ? trigger_loc : 0; 
        end

        else if(state == MOVE_TO_POSITION) begin
            // if trigger location is negative or zero,
            // then we're already in position
            if(trigger_loc <= 0) state <= IN_POSITION;

            // otherwise we'll need to wait a little,
            // but we'll need to buffer along the way
            else begin
                present_loc <= present_loc + 1;
                // add code to add samples to word FIFO
                wfifo_in_valid <= 1;
                if (present_loc == trigger_loc) state <= IN_POSITION; 
            end
        end

        else if(state == IN_POSITION) begin
            // pop stuff out of the word FIFO in addition to pulling it in
            wfifo_in_valid <= 1;
            wfifo_out_req <= 1;

            if(triggered) state <= FILLING_BUFFER;
        end

        else if(state == FILLING_BUFFER) begin
            if(wfifo_size == SAMPLE_DEPTH) state <= FILLED;
        end

        else if(state == FILLED) begin
            // don't automatically go back to IDLE, the host will move
            // the state to MOVE_TO_POSITION

            present_loc <= (trigger_loc < 0) ? trigger_loc : 0; 
        end
    end



    // memory servicing
    //  - TODO: add support for comparision values > 16 bits,
    //    we'll have to concat them somwehere up here

    always @(posedge clk) begin

        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;

        // operations to configuration registers        
        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 9) ) begin
            
            // reads
            if(valid_i && !rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: rdata_o <= state;
                    BASE_ADDR + 1: rdata_o <= trigger_loc;
                    BASE_ADDR + 2: rdata_o <= larry_trigger_op;
                    BASE_ADDR + 3: rdata_o <= larry_trigger_arg;
                    BASE_ADDR + 4: rdata_o <= curly_trigger_op;
                    BASE_ADDR + 5: rdata_o <= curly_trigger_arg;
                    BASE_ADDR + 6: rdata_o <= moe_trigger_op;
                    BASE_ADDR + 7: rdata_o <= moe_trigger_arg;
                    BASE_ADDR + 8: rdata_o <= shemp_trigger_op;
                    BASE_ADDR + 9: rdata_o <= shemp_trigger_arg;
                    default: rdata_o <= rdata_i;
                endcase
            end

            // writes
            else if(valid_i && rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: state <= wdata_i;
                    BASE_ADDR + 1: trigger_loc <= wdata_i;
                    BASE_ADDR + 2: larry_trigger_op <= wdata_i;
                    BASE_ADDR + 3: larry_trigger_arg <= wdata_i;
                    BASE_ADDR + 4: curly_trigger_op <= wdata_i;
                    BASE_ADDR + 5: curly_trigger_arg <= wdata_i;
                    BASE_ADDR + 6: moe_trigger_op <= wdata_i;
                    BASE_ADDR + 7: moe_trigger_arg <= wdata_i;
                    BASE_ADDR + 8: shemp_trigger_op <= wdata_i;
                    BASE_ADDR + 9: shemp_trigger_arg <= wdata_i;
                    default: wdata_o <= wdata_i; 
                endcase
            end
        end

        // operations to BRAM
        else if( (addr_i >= BASE_ADDR + 10) && (addr_i <= BASE_ADDR + 10 + SAMPLE_DEPTH) ) begin
        end
    end
endmodule

`default_nettype wire