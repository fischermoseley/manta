`default_nettype none
`timescale 1ns/1ps

module lut_ram(
    input wire clk,

    // input port
    input wire req_addr_i,
    input wire req_data_i,
    input wire req_rw_i,
    input wire req_valid_i,
    output reg req_ready_o

    input wire res_data_i,
    input wire res_valid_i,
    output reg res_ready_o

    // output port
    output reg req_addr_o,
    output reg req_data_o,
    output reg req_rw_o,
    output reg req_valid_o,
    input wire req_ready_i,

    output reg res_data_o,
    output reg res_valid_o,
    input wire res_ready_i
);

localparam BASE_ADDR = 0;
localparam DEPTH = 8;
localparam TOP_ADDR = BASE_ADDR + DEPTH - 1;

reg [15:0] [DEPTH-1:0] mem;

initial begin
    req_ready_o = 1;
end

always @(posedge clk) begin
    if( (req_addr_i < BASE_ADDR) || (req_addr_i > TOP_ADDR) ) begin
        req_addr_o <= req_addr_i;
        req_data_o <= req_data_i;
        req_rw_o <= req_rw_i;
        req_valid_o <= req_valid_i;
        req_ready_o <= req_ready_i;

        res_data_o <= res_data_i;
        res_valid_o <= res_valid_i;
        res_ready_o <= res_ready_i;
    end

    else begin
        req_ready <= 1;


        if (req_valid_i) begin
            if (req_rw_i) mem[req_addr_i - BASE_ADDR] <= req_data_i;

            else begin
                 
            end
        end
    end
end

endmodule


`default_nettype wire