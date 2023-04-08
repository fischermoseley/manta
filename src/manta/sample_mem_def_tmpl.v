`default_nettype none
`timescale 1ns/1ps

module sample_mem (
    input wire clk,

    // fifo
    input wire acquire,
    input wire pop,
    output logic [BRAM_ADDR_WIDTH:0] size,
    input wire clear,

    // probes
    /* PROBE_PORTS */

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
    output reg valid_o);

    parameter BASE_ADDR = 0;
    parameter SAMPLE_DEPTH = 0;
    localparam BRAM_ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    // bus controller
    reg [BRAM_ADDR_WIDTH-1:0] bram_read_addr;
    reg [15:0] bram_read_data;

    always @(*) begin
        // if address is valid
        if ( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + SAMPLE_DEPTH) ) begin

            // figure out proper place to read from
            // want to read from the read pointer, and then loop back around
            if(read_pointer + (addr_i - BASE_ADDR) > SAMPLE_DEPTH)
                bram_read_addr = read_pointer + (addr_i - BASE_ADDR) - SAMPLE_DEPTH;

            else
                bram_read_addr = read_pointer + (addr_i - BASE_ADDR);
        end

        else bram_read_addr = 0;
    end


    // pipeline bus to compensate for 2-cycles of delay in BRAM
    reg [15:0] addr_pip;
    reg [15:0] wdata_pip;
    reg [15:0] rdata_pip;
    reg rw_pip;
    reg valid_pip;

    always @(posedge clk) begin
        addr_pip <= addr_i;
        wdata_pip <= wdata_i;
        rdata_pip <= rdata_i;
        rw_pip <= rw_i;
        valid_pip <= valid_i;

        addr_o <= addr_pip;
        wdata_o <= wdata_pip;
        rdata_o <= rdata_pip;
        rw_o <= rw_pip;
        valid_o <= valid_pip;

        if( valid_pip && !rw_pip && (addr_pip >= BASE_ADDR) && (addr_pip <= BASE_ADDR + SAMPLE_DEPTH) )
            rdata_o <= bram_read_data;
    end


    // bram
    dual_port_bram #(
		.RAM_WIDTH(16),
		.RAM_DEPTH(SAMPLE_DEPTH)
    ) bram (
		// read port (controlled by bus)
		.clka(clk),
		.addra(bram_read_addr),
		.dina(16'b0),
		.wea(1'b0),
		.douta(bram_read_data),

		// write port (controlled by FIFO)
		.clkb(clk),
		.addrb(write_pointer[BRAM_ADDR_WIDTH-1:0]),
		.dinb(/* CONCAT */),
		.web(acquire),
		.doutb());


    // fifo
	reg [BRAM_ADDR_WIDTH:0] write_pointer = 0;
	reg [BRAM_ADDR_WIDTH:0] read_pointer = 0;

	assign size = write_pointer - read_pointer;

	always @(posedge clk) begin
        if (clear) read_pointer <= write_pointer;
		if (acquire && size < SAMPLE_DEPTH) write_pointer <= write_pointer + 1'd1;
	 	if (pop && size > 0) read_pointer <= read_pointer + 1'd1;
	end
endmodule

`default_nettype wire