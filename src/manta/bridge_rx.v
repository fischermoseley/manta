`default_nettype none
`timescale 1ns/1ps

module bridge_rx(
    input wire clk,
    input wire rst,

    input wire[7:0] axiid,
    input wire axiiv,

    output reg[15:0] req_addr,
    output reg[15:0] req_data,
    output reg req_rw,
    output reg req_valid,
    input wire req_ready
);

parameter ADDR_WIDTH = 0;
parameter DATA_WIDTH = 0;

localparam PREAMBLE = 8'h4D;
localparam CR = 8'h0D;
localparam LF = 8'h0A;

localparam ACQUIRE = 0;
localparam TRANSMIT = 1;
localparam ERROR = 2;

reg [1:0] state;
reg [3:0] bytes_received;

// no global resets!
initial begin
    req_addr = 0;
    req_data = 0;
    req_rw = 0;
    req_valid = 0;
    bytes_received = 0;
    state = ACQUIRE;
end

reg [3:0] axiid_decoded;
reg axiid_is_0_thru_9;
reg axiid_is_A_thru_F;

always @(*) begin
    axiid_is_0_thru_9 = (axiid >= 8'h30) & (axiid <= 8'h39);
    axiid_is_A_thru_F = (axiid >= 8'h41) & (axiid <= 8'h46);

    if (axiid_is_0_thru_9) axiid_decoded = axiid - 8'h30;
    else if (axiid_is_A_thru_F) axiid_decoded = axiid - 8'h41 + 'd10;
    else axiid_decoded = 0;
end


always @(posedge clk) begin
    if (state == ACQUIRE) begin
        if(axiiv) begin

            if (bytes_received == 0) begin
                if(axiid == PREAMBLE) bytes_received <= 1;
            end

            else if( (bytes_received >= 1) & (bytes_received <= 4) ) begin
                // only advance if byte is valid hex digit
                if(axiid_is_0_thru_9 | axiid_is_A_thru_F) begin
                    req_addr <= (req_addr << 4) | axiid_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if( bytes_received == 5) begin
                    if( (axiid == CR) | (axiid == LF)) begin
                        req_valid <= 1;
                        req_rw = 0;
                        bytes_received <= 0;
                        state <= TRANSMIT;
                    end

                    else if (axiid_is_0_thru_9 | axiid_is_A_thru_F) begin
                        bytes_received <= bytes_received + 1;
                        req_data <= (req_data << 4) | axiid_decoded;
                    end

                    else state <= ERROR;
            end

            else if ( (bytes_received >= 6) & (bytes_received <= 8) ) begin

                if (axiid_is_0_thru_9 | axiid_is_A_thru_F) begin
                    req_data <= (req_data << 4) | axiid_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if (bytes_received == 9) begin
                bytes_received <= 0;
                if( (axiid == CR) | (axiid == LF)) begin
                    req_valid <= 1;
                    req_rw <= 1;
                    state <= TRANSMIT;
                end

                else state <= ERROR;
            end
        end
    end


    else if (state == TRANSMIT) begin
        if(req_ready) begin
            req_valid <= 0;
            state <= ACQUIRE;
        end

        if(axiiv) begin
            if ( (axiid != CR) & (axiid != LF)) begin
                req_valid <= 0;
                state <= ERROR;
            end
        end
    end
end

endmodule
`default_nettype wire