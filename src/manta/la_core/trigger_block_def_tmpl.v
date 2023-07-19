`default_nettype none
`timescale 1ns/1ps

module trigger_block (
    input wire clk,

    // probes
    /* PROBE_PORTS */

    // trigger
    output reg trig,

    // input port
    input wire [15:0] addr_i,
    input wire [15:0] data_i,
    input wire rw_i,
    input wire valid_i,

    // output port
    output reg [15:0] addr_o,
    output reg [15:0] data_o,
    output reg rw_o,
    output reg valid_o);

    parameter BASE_ADDR = 0;
    localparam MAX_ADDR = /* MAX_ADDR */;

    // trigger configuration registers
    // - each probe gets an operation and a compare register
    // - at the end we OR them all together. along with any custom probes the user specs

    /* TRIGGER_MODULE_INSTS */

    /* COMBINE_INDIV_TRIGGERS */

    // perform register operations
    always @(posedge clk) begin
        addr_o <= addr_i;
        data_o <= data_i;
        rw_o <= rw_i;
        valid_o <= valid_i;

        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + MAX_ADDR) ) begin

            // reads
            if(valid_i && !rw_i) begin
                case (addr_i)
                    /* READ_CASE_STATEMENT_BODY */
                endcase
            end

            // writes
            else if(valid_i && rw_i) begin
                case (addr_i)
                    /* WRITE_CASE_STATEMENT_BODY */
                endcase
            end
        end
    end
endmodule

`default_nettype wire