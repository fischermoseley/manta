`default_nettype none
`timescale 1ns/1ps

module bridge_tx (
    input wire clk,

    input wire [15:0] data_i,
    input wire rw_i,
    input wire valid_i,

    output reg [7:0] data_o,
    output reg start_o,
    input wire done_i);

    function [7:0] to_ascii_hex;
        // convert a number from 0-15 into the corresponding ascii char
        input [3:0] n;
        to_ascii_hex = (n < 10) ? (n + 8'h30) : (n + 8'h41 - 'd10);
    endfunction

    localparam PREAMBLE = "D";
    localparam CR = 8'h0D;
    localparam LF = 8'h0A;

    reg busy = 0;
    reg [15:0] buffer = 0;
    reg [3:0] count = 0;

    assign start_o = busy;

    always @(posedge clk) begin
        // idle until valid read transaction arrives on bus
        if (!busy) begin
            if (valid_i && !rw_i) begin
                busy <= 1;
                buffer <= data_i;
            end
        end

        if (busy) begin
            // uart module is done transmitting a byte
            if(done_i) begin
                count <= count + 1;

                // message has been transmitted
                if (count > 5) begin
                    count <= 0;

                    // go back to idle or transmit next message
                    if (valid_i && !rw_i) buffer <= data_i;
                    else busy <= 0;
                end
            end
        end
    end

    always @(*) begin
        case (count)
            0: data_o = PREAMBLE;
            1: data_o = to_ascii_hex(buffer[15:12]);
            2: data_o = to_ascii_hex(buffer[11:8]);
            3: data_o = to_ascii_hex(buffer[7:4]);
            4: data_o = to_ascii_hex(buffer[3:0]);
            5: data_o = CR;
            6: data_o = LF;
            default: data_o = 0;
        endcase
    end
endmodule
`default_nettype wire