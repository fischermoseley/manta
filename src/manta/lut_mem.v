`default_nettype none
`timescale 1ns/1ps

module lut_mem(
    input wire clk,

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


parameter DEPTH = 8;
parameter BASE_ADDR = 0;
reg [DEPTH-1:0][15:0] mem;

reg [15:0] addr_ppln;
reg [15:0] wdata_ppln;
reg [15:0] rdata_ppln;
reg rw_ppln;
reg valid_ppln;

always @(posedge clk) begin
    
    // pipeline stage 1
    addr_ppln <= addr_i;
    wdata_ppln <= wdata_i;
    rdata_ppln <= rdata_i;
    rw_ppln <= rw_i;
    valid_ppln <= valid_i;

    // pipeline stage 2
    addr_o <= addr_ppln;
    wdata_o <= wdata_ppln;
    rdata_o <= rdata_ppln;
    rw_o <= rw_ppln;
    valid_o <= valid_ppln;
    

    if(valid_i) begin
        // write to memory
        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + DEPTH - 1) ) begin

            // write to mem
            if (rw_i) mem[addr_i - BASE_ADDR] <= wdata_i;

            // read from mem
            else rdata_ppln <= mem[addr_i - BASE_ADDR];
        end
    end
end
endmodule

`default_nettype wire