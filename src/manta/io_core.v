`default_nettype none
`timescale 1ns/1ps

module io_core(
    input wire clk,

    // inputs
    input wire picard,
    input wire [6:0] data,
    input wire [9:0] laforge,
    input wire troi,

    // outputs
    output reg kirk,
    output reg [4:0] spock,
    output reg [2:0] uhura,
    output reg chekov,

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

    parameter BASE_ADDR = 0;

    initial begin
        kirk = 0;
        spock = 0;
        uhura = 0;
        chekov = 0;
    end

    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;
        

        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 7)) begin

            if(!rw_i) begin // reads
                case (addr_i)
                    BASE_ADDR + 0: rdata_o <= {15'b0, picard};
                    BASE_ADDR + 1: rdata_o <= {9'b0,  data};
                    BASE_ADDR + 2: rdata_o <= {6'b0,  laforge};
                    BASE_ADDR + 3: rdata_o <= {15'b0, troi};
                    BASE_ADDR + 4: rdata_o <= {15'b0, kirk};
                    BASE_ADDR + 5: rdata_o <= {11'b0, spock};
                    BASE_ADDR + 6: rdata_o <= {13'b0, uhura};
                    BASE_ADDR + 7: rdata_o <= {15'b0, chekov};
                endcase
            end

            else begin // writes
                case (addr_i)
                    BASE_ADDR + 4: kirk   <= wdata_i[0];
                    BASE_ADDR + 5: spock  <= wdata_i[4:0];
                    BASE_ADDR + 6: uhura  <= wdata_i[2:0];
                    BASE_ADDR + 7: chekov <= wdata_i[0];
                endcase
            end
        end
    end
endmodule

`default_nettype wire