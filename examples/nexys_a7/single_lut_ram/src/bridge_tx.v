`default_nettype none
`timescale 1ns/1ps

module bridge_tx(
    input wire clk,
    
    output reg [7:0] axiod,
    output reg axiov,
    input wire axior,

    input wire [15:0] res_data,
    input wire res_valid,
    output reg res_ready
);

parameter ADDR_WIDTH = 0;
parameter DATA_WDITH = 0;

localparam PREAMBLE = 8'h4D;
localparam CR = 8'h0D;
localparam LF = 8'h0A;

reg [3:0] bytes_transmitted;
reg [15:0] buffer;

initial begin
    axiod = 0;
    axiov = 0;
    res_ready = 1;
    bytes_transmitted = 0;
    buffer = 0;
end

always @(posedge clk) begin
    if (res_ready) begin
        if(res_valid) begin
            buffer <= res_data;
            res_ready <= 0;
            bytes_transmitted <= 0;
            axiod <= PREAMBLE;
            axiov <= 1;
        end
    end

    else begin
        if (bytes_transmitted == 0) begin
            if(axior) bytes_transmitted <= 1;
        end

        if (bytes_transmitted == 1) begin
            axiod <= (buffer[15:12] < 10) ? (buffer[15:12] + 8'h30) : (buffer[15:12] + 8'h41 - 'd10);
            if (axior) bytes_transmitted <= 2;
        end

        else if(bytes_transmitted == 2) begin
            axiod <= (buffer[11:8] < 10) ? (buffer[11:8] + 8'h30) : (buffer[11:8] + 8'h41 - 'd10);
            if (axior) bytes_transmitted <= 3;
        end

        else if(bytes_transmitted == 3) begin
            axiod <= (buffer[7:4] < 10) ? (buffer[7:4] + 8'h30) : (buffer[7:4] + 8'h41 - 'd10);
            if (axior) bytes_transmitted <= 4;
        end

        else if(bytes_transmitted == 4) begin
            axiod <= (buffer[3:0] < 10) ? (buffer[3:0] + 8'h30) : (buffer[3:0] + 8'h41 - 'd10);
            if (axior) bytes_transmitted <= 5;
        end

        else if(bytes_transmitted == 5) begin
            axiod <= 8'h0D;
            if (axior) bytes_transmitted <= 6;
        end

        else if(bytes_transmitted == 6) begin
            axiod <= 8'h0A;
            if (axior) begin
                axiov <= 0;
                res_ready <= 1;
                bytes_transmitted <= 0;
            end
        end
    end
end

endmodule
`default_nettype wire