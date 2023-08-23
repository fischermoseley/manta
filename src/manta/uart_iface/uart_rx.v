`default_nettype none
`timescale 1ns/1ps

// Modified from Dan Gisselquist's rx_uart module,
// available at https://zipcpu.com/tutorial/ex-09-uartrx.zip

module uart_rx (
    input wire clk,

    input wire rx,

    output reg [7:0] data_o,
    output reg valid_o);

    parameter CLOCKS_PER_BAUD = 0;
    localparam IDLE = 0;
    localparam BIT_ZERO = 1;
    localparam STOP_BIT = 9;

    reg	[3:0] state = IDLE;
    reg	[15:0] baud_counter = 0;
    reg zero_baud_counter;
    assign zero_baud_counter = (baud_counter == 0);

    // 2FF Synchronizer
    reg ck_uart = 1;
    reg	q_uart = 1;
    always @(posedge clk)
        { ck_uart, q_uart } <= { q_uart, rx };

    always @(posedge clk)
        if (state == IDLE) begin
            state <= IDLE;
            baud_counter <= 0;
            if (!ck_uart) begin
                state <= BIT_ZERO;
                baud_counter <= CLOCKS_PER_BAUD+CLOCKS_PER_BAUD/2-1'b1;
            end
        end

        else if (zero_baud_counter) begin
            state <= state + 1;
            baud_counter <= CLOCKS_PER_BAUD-1'b1;
            if (state == STOP_BIT) begin
                state <= IDLE;
                baud_counter <= 0;
            end
        end

        else baud_counter <= baud_counter - 1'b1;

    always @(posedge clk)
        if ( (zero_baud_counter) && (state != STOP_BIT) )
            data_o <= {ck_uart, data_o[7:1]};

    initial	valid_o = 1'b0;
    always @(posedge clk)
        valid_o <= ( (zero_baud_counter) && (state == STOP_BIT) );

endmodule

`default_nettype wire