`default_nettype none
`timescale 1ns/1ps

module bridge_tx(
    input wire clk,

    input wire [15:0] rdata_i,
    input wire rw_i,
    input wire valid_i,

    output reg [7:0] data_o,
    input wire ready_i,
    output reg valid_o);

localparam PREAMBLE = 8'h4D;
localparam CR = 8'h0D;
localparam LF = 8'h0A;

logic busy;
logic [15:0] buffer;
logic [3:0] byte_counter;

initial begin
    busy = 0;
    buffer = 0;
    byte_counter = 0; 
    valid_o = 0;
end

always @(posedge clk) begin
    if (!busy) begin
        if (valid_i && !rw_i) begin
            busy <= 1;
            buffer <= rdata_i;
            byte_counter <= 0;
            valid_o <= 1;
        end
    end

    if (busy) begin

        if(ready_i) begin
            byte_counter <= byte_counter + 1;
            
            if (byte_counter > 5) begin
                byte_counter <= 0;

                // stop transmitting if we don't have both valid and read
                if ( !(valid_i && !rw_i) ) begin
                    busy <= 0;
                    valid_o <= 0;
                end
            end
        end
    end
end

always @(*) begin
    case (byte_counter)
        0: data_o = PREAMBLE;
        1: data_o = (buffer[15:12] < 10) ? (buffer[15:12] + 8'h30) : (buffer[15:12] + 8'h41 - 'd10);
        2: data_o = (buffer[11:8] < 10) ? (buffer[11:8] + 8'h30) : (buffer[11:8] + 8'h41 - 'd10); 
        3: data_o = (buffer[7:4] < 10) ? (buffer[7:4] + 8'h30) : (buffer[7:4] + 8'h41 - 'd10);
        4: data_o = (buffer[3:0] < 10) ? (buffer[3:0] + 8'h30) : (buffer[3:0] + 8'h41 - 'd10);
        5: data_o = CR;
        6: data_o = LF;
        default: data_o = 0;
    endcase
end

endmodule
`default_nettype wire