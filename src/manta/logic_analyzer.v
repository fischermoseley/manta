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
    parameter SAMPLE_DEPTH = 0;

    // fsm
    la_fsm #(.BASE_ADDR(BASE_ADDR), .SAMPLE_DEPTH(SAMPLE_DEPTH)) fsm (
        .clk(clk),

        .trig(trig),
        .fifo_size(fifo_size),
        .fifo_acquire(fifo_acquire),
        .fifo_pop(fifo_pop),

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
     

    // trigger block
    trigger_block #(.BASE_ADDR(BASE_ADDR + 2)) trig_blk(
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
    sample_mem #(.BASE_ADDR(BASE_ADDR + 10), .SAMPLE_DEPTH(SAMPLE_DEPTH)) sample_mem(
        .clk(clk),

        // fifo
        .acquire(fifo_acquire),
        .pop(fifo_pop),
        .size(fifo_size),

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

`default_nettype wire