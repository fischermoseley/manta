module /* MODULE_NAME */ (
    input wire bus_clk,
    input wire user_clk,

    // ports
    /* TOP_LEVEL_PORTS */

    // input port
    input wire [15:0] addr_i,
    input wire [15:0] data_i,
    input wire rw_i,
    input wire valid_i,

    // output port
    output reg [15:0] addr_o,
    output reg [15:0] data_o,
    output reg rw_o,
    output reg valid_o
    );

    parameter BASE_ADDR = 0;

    reg strobe = 0;

    // input probe buffers
    /* INPUT_PROBE_BUFFERS */

    // output probe buffers
    /* OUTPUT_PROBE_BUFFERS */

    // output probe initial values
    initial begin
        /* OUTPUT_PROBE_INITIAL_VALUES */
    end

    // synchronize buffers and probes on strobe
    always @(posedge user_clk) begin
        if(strobe) begin
            // update input buffers from input probes
            /* UPDATE_INPUT_BUFFERS */

            // update output buffers from output probes
            /* UPDATE_OUTPUT_BUFFERS */
        end
    end

    // handle bus operations
    always @(posedge bus_clk) begin
        addr_o <= addr_i;
        data_o <= data_i;
        rw_o <= rw_i;
        valid_o <= valid_i;

        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + /* MAX_ADDR */)) begin

            // reads
            if(!rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: data_o <= strobe;

                    /* READ_CASE_STATEMENT_BODY */
                endcase
            end

            // writes
            else begin
                case (addr_i)
                    BASE_ADDR + 0: strobe <= data_i;

                    /* WRITE_CASE_STATEMENT_BODY */
                endcase
            end
        end
    end

endmodule