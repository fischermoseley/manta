`default_nettype none
`timescale 1ns/1ps

module logic_analyzer (
    input wire clk,

    // probes
    /* TOP_LEVEL_PROBE_PORTS */

    // input port
    input wire [15:0] addr_i,
    input wire [15:0] data_i,
    input wire rw_i,
    input wire valid_i,

    // output port
    output reg [15:0] addr_o,
    output reg [15:0] data_o,
    output reg rw_o,
    output reg valid_o
    );
    localparam SAMPLE_DEPTH = /* SAMPLE_DEPTH */;
    localparam ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    reg [3:0] state;
    reg [15:0] trigger_loc;
    reg [1:0] trigger_mode;
    reg request_start;
    reg request_stop;
    reg [ADDR_WIDTH-1:0] read_pointer;
    reg [ADDR_WIDTH-1:0] write_pointer;

    reg trig;

    reg [ADDR_WIDTH-1:0] bram_addr;
    reg bram_we;

    localparam TOTAL_PROBE_WIDTH = /* TOTAL_PROBE_WIDTH */;
    reg [TOTAL_PROBE_WIDTH-1:0] probes_concat;
    assign probes_concat = /* PROBES_CONCAT */;

    logic_analyzer_controller #(.SAMPLE_DEPTH(SAMPLE_DEPTH)) la_controller (
        .clk(clk),

        // from register file
        .state(state),
        .trigger_loc(trigger_loc),
        .trigger_mode(trigger_mode),
        .request_start(request_start),
        .request_stop(request_stop),
        .read_pointer(read_pointer),
        .write_pointer(write_pointer),

        // from trigger block
        .trig(trig),

        // from block memory user port
        .bram_addr(bram_addr),
        .bram_we(bram_we)
    );

    logic_analyzer_fsm_registers #(
        .BASE_ADDR(/* FSM_BASE_ADDR */),
        .SAMPLE_DEPTH(SAMPLE_DEPTH)
        ) fsm_registers (
        .clk(clk),

        .addr_i(addr_i),
        .data_i(data_i),
        .rw_i(rw_i),
        .valid_i(valid_i),

        .addr_o(fsm_reg_trig_blk_addr),
        .data_o(fsm_reg_trig_blk_data),
        .rw_o(fsm_reg_trig_blk_rw),
        .valid_o(fsm_reg_trig_blk_valid),

        .state(state),
        .trigger_loc(trigger_loc),
        .trigger_mode(trigger_mode),
        .request_start(request_start),
        .request_stop(request_stop),
        .read_pointer(read_pointer),
        .write_pointer(write_pointer));

    reg [15:0] fsm_reg_trig_blk_addr;
    reg [15:0] fsm_reg_trig_blk_data;
    reg fsm_reg_trig_blk_rw;
    reg fsm_reg_trig_blk_valid;

    // trigger block
    trigger_block #(.BASE_ADDR(/* TRIGGER_BLOCK_BASE_ADDR */)) trig_blk (
        .clk(clk),

        /* TRIGGER_BLOCK_PROBE_PORTS */

        .trig(trig),

        .addr_i(fsm_reg_trig_blk_addr),
        .data_i(fsm_reg_trig_blk_data),
        .rw_i(fsm_reg_trig_blk_rw),
        .valid_i(fsm_reg_trig_blk_valid),

        .addr_o(trig_blk_block_mem_addr),
        .data_o(trig_blk_block_mem_data),
        .rw_o(trig_blk_block_mem_rw),
        .valid_o(trig_blk_block_mem_valid));

    reg [15:0] trig_blk_block_mem_addr;
    reg [15:0] trig_blk_block_mem_data;
    reg trig_blk_block_mem_rw;
    reg trig_blk_block_mem_valid;

    // sample memory
    block_memory #(
        .BASE_ADDR(/* BLOCK_MEMORY_BASE_ADDR */),
        .WIDTH(TOTAL_PROBE_WIDTH),
        .DEPTH(SAMPLE_DEPTH)
        ) block_mem (
        .clk(clk),

        // input port
        .addr_i(trig_blk_block_mem_addr),
        .data_i(trig_blk_block_mem_data),
        .rw_i(trig_blk_block_mem_rw),
        .valid_i(trig_blk_block_mem_valid),

        // output port
        .addr_o(addr_o),
        .data_o(data_o),
        .rw_o(rw_o),
        .valid_o(valid_o),

        // BRAM itself
        .user_clk(clk),
        .user_addr(bram_addr),
        .user_din(probes_concat),
        .user_dout(),
        .user_we(bram_we));
endmodule

`default_nettype wire