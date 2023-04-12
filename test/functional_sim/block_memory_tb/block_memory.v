module my_bram (
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
    input wire user_clk,
    input wire [ADDR_WIDTH-1:0] user_addr,
    input wire [BRAM_WIDTH-1:0] user_din,
    output reg [BRAM_WIDTH-1:0] user_dout,
    input wire user_we);

    parameter BASE_ADDR = 0;
    localparam BRAM_WIDTH = 18;
    localparam BRAM_DEPTH = 256;
    localparam ADDR_WIDTH = $clog2(BRAM_DEPTH);

    localparam MAX_ADDR = 512;
    localparam N_BRAMS = 2;
    localparam N_FULL_WIDTH_BRAMS = 1;
    localparam PARTIAL_BRAM_WIDTH = 2;

    // Bus-Controlled side of BRAMs
    reg [N_BRAMS-1:0][ADDR_WIDTH-1:0] addra = 0;
    reg [N_BRAMS-1:0][15:0] dina = 0;
    reg [N_BRAMS-1:0][15:0] douta;
    reg [N_BRAMS-1:0] wea = 0;

    // User-Controlled Side of BRAMs
    reg [N_BRAMS-1:0][15:0] dinb = 0;
    reg [N_BRAMS-1:0][15:0] doutb;
    assign dout = {doutb[1], doutb[0]};

    // Pipelining
    reg [3:0][15:0] addr_pipe = 0;
    reg [3:0][15:0] wdata_pipe = 0;
    reg [3:0][15:0] rdata_pipe = 0;
    reg [3:0] valid_pipe = 0;
    reg [3:0] rw_pipe = 0;

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
        wea <= 0;
        if( (valid_i) && (addr_i >= BASE_ADDR) && (addr_i <= MAX_ADDR)) begin
            wea[addr_i % N_BRAMS]   <= rw_i;
            addra[addr_i % N_BRAMS] <= (addr_i - BASE_ADDR) / N_BRAMS;
            dina[addr_i % N_BRAMS]  <= wdata_i;
        end

        // pull BRAM reads from the back of the pipeline
        if( (valid_pipe[2]) && (addr_pipe[2] >= BASE_ADDR) && (addr_pipe[2] <= MAX_ADDR)) begin
            rdata_o <= douta[addr_pipe[2] % N_BRAMS];
        end
    end

    // generate the full-width BRAMs
    genvar i;
    generate
        for(i=0; i<N_FULL_WIDTH_BRAMS; i=i+1) begin
            dual_port_bram #(
                .RAM_WIDTH(16),
                .RAM_DEPTH(BRAM_DEPTH)
                ) bram_full_width_i (

                // port A is controlled by the bus
                .clka(clk),
                .addra(addra[i]),
                .dina(dina[i]),
                .douta(douta[i]),
                .wea(wea[i]),

                // port B is exposed to the user
                .clkb(user_clk),
                .addrb(user_addr),
                .dinb(dinb[i]),
                .doutb(doutb[i]),
                .web(user_we));
        end

        if(PARTIAL_BRAM_WIDTH > 0) begin
            dual_port_bram #(
                .RAM_WIDTH(PARTIAL_BRAM_WIDTH),
                .RAM_DEPTH(BRAM_DEPTH)
                ) bram_partial_width (

                // port A is controlled by the bus
                .clka(clk),
                .addra(addra[N_BRAMS-1]),
                .dina(dina[N_BRAMS-1][PARTIAL_BRAM_WIDTH-1:0]),
                .douta(douta[N_BRAMS-1]),
                .wea(wea[N_BRAMS-1]),

                // port B is exposed to the user
                .clkb(user_clk),
                .addrb(user_addr),
                .dinb(dinb[N_BRAMS-1][PARTIAL_BRAM_WIDTH-1:0]),
                .doutb(doutb[N_BRAMS-1]),
                .web(user_we));
        end
    endgenerate
endmodule