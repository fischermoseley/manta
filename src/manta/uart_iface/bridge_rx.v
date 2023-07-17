`default_nettype none
`timescale 1ns/1ps

module bridge_rx (
    input wire clk,

    input wire [7:0] data_i,
    input wire valid_i,

    output reg [15:0] addr_o,
    output reg [15:0] data_o,
    output reg rw_o,
    output reg valid_o);

    initial addr_o = 0;
    initial data_o = 0;
    initial rw_o = 0;
    initial valid_o = 0;

    function [3:0] from_ascii_hex;
        // convert an ascii char encoding a hex value to
        // the corresponding hex value
        input [7:0] c;

        if ((c >= 8'h30) && (c <= 8'h39)) from_ascii_hex = c - 8'h30;
        else if ((c >= 8'h41) && (c <= 8'h46)) from_ascii_hex = c - 8'h41 + 'd10;
        else from_ascii_hex = 0;
    endfunction

    function is_ascii_hex;
        // checks if a byte is an ascii char encoding a hex digit
        input [7:0] c;

        if ((c >= 8'h30) && (c <= 8'h39)) is_ascii_hex = 1; // 0-9
        else if ((c >= 8'h41) && (c <= 8'h46)) is_ascii_hex = 1; // A-F
        else is_ascii_hex = 0;
    endfunction

    reg [7:0] buffer [7:0]; // = 0; // todo: see if sby will tolerate packed arrays?

    localparam IDLE = 0;
    localparam READ = 1;
    localparam WRITE = 2;
    reg [1:0] state = 0;
    reg [3:0] byte_num = 0;

    always @(posedge clk) begin
        addr_o <= 0;
        data_o <= 0;
        rw_o <= 0;
        valid_o <= 0;

        if (state == IDLE) begin
            byte_num <= 0;
            if (valid_i) begin
                if (data_i == "R") state <= READ;
                if (data_i == "W") state <= WRITE;
           end
        end

        else begin
            if (valid_i) begin
                // buffer bytes regardless of if they're good
                byte_num <= byte_num + 1;
                buffer[byte_num] <= data_i;

                // current transaction specifies a read operation
                if(state == READ) begin

                    // go to idle if anything doesn't make sense
                    if(byte_num < 4) begin
                        if(!is_ascii_hex(data_i)) state <= IDLE;
                    end

                    else if(byte_num == 4) begin
                        state <= IDLE;

                        // put data on the bus if the last byte looks good
                        if((data_i == 8'h0D) || (data_i == 8'h0A)) begin
                            addr_o <=   (from_ascii_hex(buffer[0]) << 12) |
                                        (from_ascii_hex(buffer[1]) << 8)  |
                                        (from_ascii_hex(buffer[2]) << 4)  |
                                        (from_ascii_hex(buffer[3]));
                            data_o <= 0;
                            rw_o <= 0;
                            valid_o <= 1;
                        end
                    end
                end

                // current transaction specifies a write transaction
                if(state == WRITE) begin

                    // go to idle if anything doesn't make sense
                    if(byte_num < 8) begin
                        if(!is_ascii_hex(data_i)) state <= IDLE;
                    end

                    else if(byte_num == 8) begin
                        state <= IDLE;

                        // put data on the bus if the last byte looks good
                        if((data_i == 8'h0A) || (data_i == 8'h0D)) begin
                            addr_o <=   (from_ascii_hex(buffer[0]) << 12) |
                                        (from_ascii_hex(buffer[1]) << 8)  |
                                        (from_ascii_hex(buffer[2]) << 4)  |
                                        (from_ascii_hex(buffer[3]));
                            data_o <=   (from_ascii_hex(buffer[4]) << 12) |
                                        (from_ascii_hex(buffer[5]) << 8)  |
                                        (from_ascii_hex(buffer[6]) << 4)  |
                                        (from_ascii_hex(buffer[7]));
                            rw_o <= 1;
                            valid_o <= 1;
                        end
                    end
                end
            end
        end
    end

`ifdef FORMAL
        always @(posedge clk) begin
            // covers
            find_any_write_transaction: cover(rw_o == 1);
            find_any_read_transaction: cover(rw_o == 0);

            find_specific_write_transaction:
                cover(data_o == 16'h1234 && addr_o == 16'h5678 && rw_o == 1 && valid_o == 1);

            find_specific_read_transaction:
                cover(addr_o == 16'h1234 && rw_o == 0 && valid_o == 1);

            find_spacey_write_transaction:
                cover((rw_o == 1) && ($past(valid_i, 3) == 0));

            // asserts
            no_back_to_back_transactions:
                assert( ~(valid_o && $past(valid_o)) );

            no_invalid_states:
                assert(state == IDLE || state == READ || state == WRITE);

            byte_counter_only_increases:
                assert(byte_num == $past(byte_num) || byte_num == $past(byte_num) + 1 || byte_num == 0);
        end
`endif // FORMAL
endmodule


`default_nettype wire