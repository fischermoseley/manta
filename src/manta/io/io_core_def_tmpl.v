module /* MODULE_NAME */ (
    input wire clk,

    // ports
    /* TOP_LEVEL_PORTS */

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

    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;


        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + /* MAX_ADDR */)) begin

            // reads
            if(!rw_i) begin
                case (addr_i)
                    /* READ_CASE_STATEMENT_BODY */
                endcase
            end

            // writes
            else begin
                case (addr_i)
                    /* WRITE_CASE_STATEMENT_BODY */
                endcase
            end
        end
    end

endmodule