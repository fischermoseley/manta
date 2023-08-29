`default_nettype none
`timescale 1ns/1ps

module io_core(
    input wire bus_clk,
    input wire user_clk,

    // inputs
    input wire probe0,
    input wire [1:0] probe1,
    input wire [7:0] probe2,
    input wire [19:0] probe3,

    // outputs
    output reg probe4,
    output reg [1:0] probe5,
    output reg [7:0] probe6,
    output reg [19:0] probe7,

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

    // configure buffers
    // inputs
    reg probe0_buf = 0;
    reg [1:0] probe1_buf = 0;
    reg [7:0] probe2_buf = 0;
    reg [19:0] probe3_buf = 0;

    // outputs
    reg probe4_buf = 1; // PROBE4_INITIAL_VALUE;
    reg [1:0] probe5_buf = 3; // PROBE5_INITIAL_VALUE;
    reg [7:0] probe6_buf = 6; // PROBE6_INITIAL_VALUE;
    reg [19:0] probe7_buf = 7; // PROBE7_INITIAL_VALUE;

    initial begin
        probe4 = 1; // PROBE4_INITIAL_VALUE;
        probe5 = 3; // PROBE5_INITIAL_VALUE;
        probe6 = 6; // PROBE6_INITIAL_VALUE;
        probe7 = 7; // PROBE7_INITIAL_VALUE;
    end

    // synchronize buffers and probes on strobe
    always @(posedge user_clk) begin
        if(strobe) begin
            // update input buffers from input probes
            probe0_buf <= probe0;
            probe1_buf <= probe1;
            probe2_buf <= probe2;
            probe3_buf <= probe3;

            // update output buffers from output probes
            probe4 <= probe4_buf;
            probe5 <= probe5_buf;
            probe6 <= probe6_buf;
            probe7 <= probe7_buf;
        end
    end


    // handle bus operations
    always @(posedge bus_clk) begin
        addr_o <= addr_i;
        data_o <= data_i;
        rw_o <= rw_i;
        valid_o <= valid_i;

        // check if address is valid
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + 10)) begin

            if(!rw_i) begin // reads
                case (addr_i)
                    BASE_ADDR + 0: data_o <= strobe;

                    BASE_ADDR + 1: data_o <= probe0_buf; // width 1
                    BASE_ADDR + 2: data_o <= probe1_buf; // width 2
                    BASE_ADDR + 3: data_o <= probe2_buf; // width 8
                    BASE_ADDR + 4: data_o <= probe3_buf[15:0]; // width 20
                    BASE_ADDR + 5: data_o <= probe3_buf[19:16];

                    BASE_ADDR + 6: data_o <= probe4_buf; // width 1
                    BASE_ADDR + 7: data_o <= probe5_buf; // width 2
                    BASE_ADDR + 8: data_o <= probe6_buf; // width 8
                    BASE_ADDR + 9: data_o <= probe7_buf[15:0]; // width 20
                    BASE_ADDR + 10: data_o <= probe7_buf[19:16];
                endcase
            end

            else begin // writes
                case (addr_i)
                    BASE_ADDR + 0: strobe <= data_i[0];

                    BASE_ADDR + 6: probe4_buf <= data_i[0];
                    BASE_ADDR + 7: probe5_buf <= data_i[1:0];
                    BASE_ADDR + 8: probe6_buf <= data_i[7:0];
                    BASE_ADDR + 9: probe7_buf[15:0] <= data_i;
                    BASE_ADDR + 10: probe7_buf[19:16] <= data_i[3:0];
                endcase
            end
        end
    end
endmodule

`default_nettype wire