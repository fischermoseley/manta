`default_nettype none
`timescale 1ns/1ps

module trigger_block(
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

    // trigger configuration registers
    // - each probe gets an operation and a compare register
    // - at the end we OR them all together. along with any custom probes the user specs

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

    // perform register operations
    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;

        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 9) ) begin
            
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

`default_nettype wire