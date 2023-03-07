`default_nettype none
`timescale 1ns/1ps

module bridge_rx(
    input wire clk,

    input wire[7:0] rx_data,
    input wire rx_valid,

    output reg[15:0] addr_o,
    output reg[15:0] wdata_o,
    output reg rw_o,
    output reg valid_o
);


// this is a hack, the FSM needs to be updated
// but this will bypass it for now
parameter ready_i = 1;

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
    addr_o = 0;
    wdata_o = 0;
    rw_o = 0;
    valid_o = 0;
    bytes_received = 0;
    state = ACQUIRE;
end

reg [3:0] rx_data_decoded;
reg rx_data_is_0_thru_9;
reg rx_data_is_A_thru_F;

always @(*) begin
    rx_data_is_0_thru_9 = (rx_data >= 8'h30) & (rx_data <= 8'h39);
    rx_data_is_A_thru_F = (rx_data >= 8'h41) & (rx_data <= 8'h46);

    if (rx_data_is_0_thru_9) rx_data_decoded = rx_data - 8'h30;
    else if (rx_data_is_A_thru_F) rx_data_decoded = rx_data - 8'h41 + 'd10;
    else rx_data_decoded = 0;
end


always @(posedge clk) begin
    if (state == ACQUIRE) begin
        if(rx_valid) begin

            if (bytes_received == 0) begin
                if(rx_data == PREAMBLE) bytes_received <= 1;
            end

            else if( (bytes_received >= 1) & (bytes_received <= 4) ) begin
                // only advance if byte is valid hex digit
                if(rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                    addr_o <= (addr_o << 4) | rx_data_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if( bytes_received == 5) begin
                    if( (rx_data == CR) | (rx_data == LF)) begin
                        valid_o <= 1;
                        rw_o = 0;
                        bytes_received <= 0;
                        state <= TRANSMIT;
                    end

                    else if (rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                        bytes_received <= bytes_received + 1;
                        wdata_o <= (wdata_o << 4) | rx_data_decoded;
                    end

                    else state <= ERROR;
            end

            else if ( (bytes_received >= 6) & (bytes_received <= 8) ) begin

                if (rx_data_is_0_thru_9 | rx_data_is_A_thru_F) begin
                    wdata_o <= (wdata_o << 4) | rx_data_decoded;
                    bytes_received <= bytes_received + 1;
                end

                else state <= ERROR;
            end

            else if (bytes_received == 9) begin
                bytes_received <= 0;
                if( (rx_data == CR) | (rx_data == LF)) begin
                    valid_o <= 1;
                    rw_o <= 1;
                    state <= TRANSMIT;
                end

                else state <= ERROR;
            end
        end
    end


    else if (state == TRANSMIT) begin
        if(ready_i) begin
            valid_o <= 0;
            state <= ACQUIRE;
        end

        if(rx_valid) begin
            if ( (rx_data != CR) & (rx_data != LF)) begin
                valid_o <= 0;
                state <= ERROR;
            end
        end
    end
end

endmodule
`default_nettype wire