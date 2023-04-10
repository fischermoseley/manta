`default_nettype none
`timescale 1ns/1ps

module bram_core (
    input wire clk,

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
    output reg valid_o,

    // BRAM itself
    input wire bram_clk,
    input wire [ADDR_WIDTH-1:0] addr,
    input wire [BRAM_WIDTH-1:0] din,
    output reg [BRAM_WIDTH-1:0] dout,
    input wire we);

    parameter BASE_ADDR = 0;


    // for now, let's pretend that this bram has a width of 33, and a depth of 256
    // parameter BRAM_WIDTH = 0;
    // parameter BRAM_DEPTH = 0;
    parameter BRAM_WIDTH = 18;
    parameter BRAM_DEPTH = 256;
    localparam ADDR_WIDTH = $clog2(BRAM_DEPTH);

    // Bus-Controlled side of BRAMs
    localparam N_BRAMS = 2;
    reg [ADDR_WIDTH-1:0] addra [N_BRAMS-1:0];
    reg [15:0] dina  [N_BRAMS-1:0];
    reg [15:0] douta [N_BRAMS-1:0];
    reg wea [N_BRAMS-1:0];

    // reg [N_BRAMS-1:0][ADDR_WIDTH-1:0] addra = 0;
    // reg [N_BRAMS-1:0][15:0] dina = 0;
    // reg [N_BRAMS-1:0][15:0] douta;
    // reg [N_BRAMS-1:0] wea = 0;

    // this will work by having each BRAM's porta signals
    // wrapped up in the stuff above, and then for the
    // stubby BRAM at the end we'll just mask off dina and dout

    // Pipelining
    reg [15:0] addr_pipe [3:0];
    reg [15:0] wdata_pipe [3:0];
    reg [15:0] rdata_pipe [3:0];
    reg valid_pipe [3:0];
    reg rw_pipe [3:0];

    // reg [15:0][3:0] addr_pipe = 0;
    // reg [15:0][3:0] wdata_pipe = 0;
    // reg [15:0][3:0] rdata_pipe = 0;
    // reg [3:0] valid_pipe = 0;
    // reg [3:0] rw_pipe = 0;

    always @(posedge clk) begin
        addr_pipe[0] <= addr_i;
        wdata_pipe[0] <= wdata_i;
        rdata_pipe[0] <= rdata_i;
        valid_pipe[0] <= valid_i;
        rw_pipe[0] <= rw_i;

        addr_o <= addr_pipe[2];
        wdata_o <= wdata_pipe[2];
        rdata_o <= rdata_pipe[2];
        valid_o <= valid_pipe[2];
        rw_o <= rw_pipe[2];

        for(int i=1; i<4; i=i+1) begin
            addr_pipe[i] <= addr_pipe[i-1];
            wdata_pipe[i] <= wdata_pipe[i-1];
            rdata_pipe[i] <= rdata_pipe[i-1];
            valid_pipe[i] <= valid_pipe[i-1];
            rw_pipe[i] <= rw_pipe[i-1];
        end

        // throw BRAM operations into the front of the pipeline
        wea[0] <= 0;
        wea[1] <= 0;
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + (2 * BRAM_DEPTH))) begin
            wea[addr_i % N_BRAMS]   <= rw_i;
            addra[addr_i % N_BRAMS] <= (addr_i - BASE_ADDR) / N_BRAMS;
            dina[addr_i % N_BRAMS]  <= wdata_i;
        end

        // pull BRAM reads from the back of the pipeline
        if( (valid_pipe[2]) && (addr_pipe[2] >= BASE_ADDR) && (addr_pipe[2] <= BASE_ADDR + (2 * BRAM_DEPTH))) begin
            rdata_o <= douta[ addr_pipe[2] % N_BRAMS];
        end
    end


    // User-Controlled Side of BRAMs

    reg [15:0] dinb_0;
    reg [15:0] doutb_0;
    reg [1:0] dinb_1;
    reg [1:0] doutb_1;

    assign dinb_0 = din[15:0];
    assign dinb_1 = din[17:16];
    assign dout = {doutb_1, doutb_0};

    dual_port_bram #(
        .RAM_WIDTH(16),
        .RAM_DEPTH(BRAM_DEPTH)
        ) bram_0 (

        // port A is controlled by the bus
        .clka(clk),
        .addra(addra[0]),
        .dina(dina[0]),
        .douta(douta[0]),
        .wea(wea[0]),

        // port B is exposed to the user
        .clkb(bram_clk),
        .addrb(addr),
        .dinb(dinb_0),
        .doutb(doutb_0),
        .web(we));

    reg [1:0] stub_bram_douta;
    assign douta[N_BRAMS-1] = {14'b0, stub_bram_douta};

    dual_port_bram #(
        .RAM_WIDTH(2),
        .RAM_DEPTH(BRAM_DEPTH)
        ) bram_1 (

        // port A is controlled by the bus
        .clka(clk),
        .addra(addra[1]),
        .dina(dina[1][1:0]),
        .douta(stub_bram_douta),
        .wea(wea[1]),

        // port B is exposed to the user
        .clkb(bram_clk),
        .addrb(addr),
        .dinb(dinb_1),
        .doutb(doutb_1),
        .web(we));


endmodule
`default_nettype wire