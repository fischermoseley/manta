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

always @(posedge clk) begin
    addr_o <= addr_i;
    wdata_o <= wdata_i;
    rdata_o <= rdata_i;
    rw_o <= rw_i;
    valid_o <= valid_i;
    rdata_o <= rdata_i;
    

    if(valid_i) begin
        // check if address is valid
        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + DEPTH - 1) ) begin
            
            // read/write
            if (rw_i) mem[addr_i - BASE_ADDR] <= wdata_i;
            else rdata_o <= mem[addr_i - BASE_ADDR];
        end
    end
end
endmodule

`default_nettype wire