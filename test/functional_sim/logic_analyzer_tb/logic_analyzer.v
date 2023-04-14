module logic_analyzer (
    input wire clk,

    // probes
    input wire larry,
    input wire curly,
    input wire moe,
    input wire [3:0] shemp,

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
    localparam SAMPLE_DEPTH = 128;
    localparam ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    reg [3:0] state;
    reg signed [15:0] trigger_loc;
    reg signed [15:0] current_loc;
    reg request_start;
    reg request_stop;
    reg [ADDR_WIDTH-1:0] read_pointer;

    reg trig;

    reg [ADDR_WIDTH-1:0] bram_addr;
    reg bram_we;

    localparam TOTAL_PROBE_WIDTH = 7;
    reg [TOTAL_PROBE_WIDTH-1:0] probes_concat;
    assign probes_concat = {larry, curly, moe, shemp};

    logic_analyzer_controller #(.SAMPLE_DEPTH(SAMPLE_DEPTH)) la_controller (
        .clk(clk),

        // from register file
        .state(state),
        .trigger_loc(trigger_loc),
        .current_loc(current_loc),
        .request_start(request_start),
        .request_stop(request_stop),
        .read_pointer(read_pointer),

        // from trigger block
        .trig(trig),

        // from block memory user port
        .bram_addr(bram_addr),
        .bram_we(bram_we)
    );

    logic_analyzer_fsm_registers #(
        .BASE_ADDR(0),
        .SAMPLE_DEPTH(SAMPLE_DEPTH)
        ) fsm_registers (
        .clk(clk),

        .addr_i(addr_i),
        .wdata_i(wdata_i),
        .rdata_i(rdata_i),
        .rw_i(rw_i),
        .valid_i(valid_i),

        .addr_o(fsm_reg_trig_blk_addr),
        .wdata_o(fsm_reg_trig_blk_wdata),
        .rdata_o(fsm_reg_trig_blk_rdata),
        .rw_o(fsm_reg_trig_blk_rw),
        .valid_o(fsm_reg_trig_blk_valid),

        .state(state),
        .trigger_loc(trigger_loc),
        .current_loc(current_loc),
        .request_start(request_start),
        .request_stop(request_stop),
        .read_pointer(read_pointer));

    reg [15:0] fsm_reg_trig_blk_addr;
    reg [15:0] fsm_reg_trig_blk_wdata;
    reg [15:0] fsm_reg_trig_blk_rdata;
    reg fsm_reg_trig_blk_rw;
    reg fsm_reg_trig_blk_valid;

    // trigger block
    trigger_block #(.BASE_ADDR(6)) trig_blk (
        .clk(clk),

        .larry(larry),
        .curly(curly),
        .moe(moe),
        .shemp(shemp),

        .trig(trig),

        .addr_i(fsm_reg_trig_blk_addr),
        .wdata_i(fsm_reg_trig_blk_wdata),
        .rdata_i(fsm_reg_trig_blk_rdata),
        .rw_i(fsm_reg_trig_blk_rw),
        .valid_i(fsm_reg_trig_blk_valid),

        .addr_o(trig_blk_block_mem_addr),
        .wdata_o(trig_blk_block_mem_wdata),
        .rdata_o(trig_blk_block_mem_rdata),
        .rw_o(trig_blk_block_mem_rw),
        .valid_o(trig_blk_block_mem_valid));

    reg [15:0] trig_blk_block_mem_addr;
    reg [15:0] trig_blk_block_mem_wdata;
    reg [15:0] trig_blk_block_mem_rdata;
    reg trig_blk_block_mem_rw;
    reg trig_blk_block_mem_valid;

    // sample memory
    block_memory #(
        .BASE_ADDR(14),
        .WIDTH(TOTAL_PROBE_WIDTH),
        .DEPTH(SAMPLE_DEPTH)
        ) block_mem (
        .clk(clk),

        // input port
        .addr_i(trig_blk_block_mem_addr),
        .wdata_i(trig_blk_block_mem_wdata),
        .rdata_i(trig_blk_block_mem_rdata),
        .rw_i(trig_blk_block_mem_rw),
        .valid_i(trig_blk_block_mem_valid),

        // output port
        .addr_o(addr_o),
        .wdata_o(wdata_o),
        .rdata_o(rdata_o),
        .rw_o(rw_o),
        .valid_o(valid_o),

        // BRAM itself
        .user_clk(clk),
        .user_addr(bram_addr),
        .user_din(probes_concat),
        .user_dout(),
        .user_we(bram_we));
endmodule
module logic_analyzer_controller (
    input wire clk,

    // from register file
    output reg [3:0] state,
    input wire signed [15:0] trigger_loc,
    output reg signed [15:0] current_loc,
    input wire request_start,
    input wire request_stop,
    output reg [ADDR_WIDTH-1:0] read_pointer,

    // from trigger block
    input wire trig,

    // block memory user port
    output [ADDR_WIDTH-1:0] bram_addr,
    output bram_we
    );

    assign bram_addr = write_pointer;
    assign bram_we = acquire;

    parameter SAMPLE_DEPTH= 0;
    localparam ADDR_WIDTH = $clog2(SAMPLE_DEPTH);

    /* ----- FSM ----- */
    localparam IDLE = 0;
    localparam MOVE_TO_POSITION = 1;
    localparam IN_POSITION = 2;
    localparam CAPTURING = 3;
    localparam CAPTURED = 4;

    initial state = IDLE;
    initial current_loc = 0;

    // rising edge detection for start/stop requests
    reg prev_request_start;
    always @(posedge clk) prev_request_start <= request_start;

    reg prev_request_stop;
    always @(posedge clk) prev_request_stop <= request_stop;

    always @(posedge clk) begin
        // don't do anything to the FIFO unless told to
        acquire <= 0;
        pop <= 0;

        if(state == IDLE) begin
            clear <= 1;

            if(request_start && ~prev_request_start) begin
                // TODO: figure out what determines whether or not we
                // go into MOVE_TO_POSITION or IN_POSITION. that's for
                // the morning
                state <= MOVE_TO_POSITION;
                clear <= 0;
            end
        end

        else if(state == MOVE_TO_POSITION) begin
            acquire <= 1;
            current_loc <= current_loc + 1;

            if(current_loc == trigger_loc) state <= IN_POSITION;
        end

        else if(state == IN_POSITION) begin
            acquire <= 1;
            pop <= 1;

            if(trig) pop <= 0;
            if(trig) state <= CAPTURING;
        end

        else if(state == CAPTURING) begin
            acquire <= 1;

            if(size == SAMPLE_DEPTH) begin
                state <= CAPTURED;
                acquire <= 0;
            end
        end

        else if(state == CAPTURED) begin
            // actually nothing to do here doooodeeedoooo
        end

        else if(request_stop && ~prev_request_stop) state <= IDLE;

        else state <= IDLE;
    end


    /* ----- FIFO ----- */
    reg acquire;
    reg pop;
    reg [ADDR_WIDTH:0] size;
    reg clear;

	reg [ADDR_WIDTH:0] write_pointer = 0;
    initial read_pointer = 0;
    initial write_pointer = 0;

	assign size = write_pointer - read_pointer;

	always @(posedge clk) begin
        if (clear) read_pointer <= write_pointer;
		if (acquire && size < SAMPLE_DEPTH) write_pointer <= write_pointer + 1'd1;
	 	if (pop && size > 0) read_pointer <= read_pointer + 1'd1;
	end
endmodule
module block_memory (
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
    input wire [WIDTH-1:0] user_din,
    output reg [WIDTH-1:0] user_dout,
    input wire user_we);

    parameter BASE_ADDR = 0;
    parameter WIDTH = 0;
    parameter DEPTH = 0;
    localparam ADDR_WIDTH = $clog2(DEPTH);

    // ugly typecasting, but just computes ceil(WIDTH / 16)
    localparam N_BRAMS = int'($ceil(real'(WIDTH) / 16.0));
    localparam MAX_ADDR = BASE_ADDR + (DEPTH * N_BRAMS);

    // Port A of BRAMs
    reg [N_BRAMS-1:0][ADDR_WIDTH-1:0] addra = 0;
    reg [N_BRAMS-1:0][15:0] dina = 0;
    reg [N_BRAMS-1:0][15:0] douta;
    reg [N_BRAMS-1:0] wea = 0;

    // Port B of BRAMs
    reg [N_BRAMS-1:0][15:0] dinb;
    reg [N_BRAMS-1:0][15:0] doutb;
    assign dinb = user_din;

    // kind of a hack to part select from a 2d array that's been flattened to 1d
    reg [(N_BRAMS*16)-1:0] doutb_flattened;
    assign doutb_flattened = doutb;
    assign user_dout = doutb_flattened[WIDTH-1:0];

    // Pipelining
    reg [2:0][15:0] addr_pipe = 0;
    reg [2:0][15:0] wdata_pipe = 0;
    reg [2:0][15:0] rdata_pipe = 0;
    reg [2:0] valid_pipe = 0;
    reg [2:0] rw_pipe = 0;

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

        for(int i=1; i<3; i=i+1) begin
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

    // generate the BRAMs
    genvar i;
    generate
        for(i=0; i<N_BRAMS; i=i+1) begin
            dual_port_bram #(
                .RAM_WIDTH(16),
                .RAM_DEPTH(DEPTH)
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
    endgenerate
endmodule
//  Xilinx True Dual Port RAM, Read First, Dual Clock
//  This code implements a parameterizable true dual port memory (both ports can read and write).
//  The behavior of this RAM is when data is written, the prior memory contents at the write
//  address are presented on the output port.  If the output data is
//  not needed during writes or the last read value is desired to be retained,
//  it is suggested to use a no change RAM as it is more power efficient.
//  If a reset or enable is not necessary, it may be tied off or removed from the code.

//  Modified from the xilinx_true_dual_port_read_first_2_clock_ram verilog language template.

module dual_port_bram #(
    parameter RAM_WIDTH = 0,
    parameter RAM_DEPTH = 0
    ) (
    input wire [$clog2(RAM_DEPTH-1)-1:0] addra,
    input wire [$clog2(RAM_DEPTH-1)-1:0] addrb,
    input wire [RAM_WIDTH-1:0] dina,
    input wire [RAM_WIDTH-1:0] dinb,
    input wire clka,
    input wire clkb,
    input wire wea,
    input wire web,
    output wire [RAM_WIDTH-1:0] douta,
    output wire [RAM_WIDTH-1:0] doutb
    );

    // The following code either initializes the memory values to a specified file or to all zeros to match hardware
    generate
        integer i;
        initial begin
            for (i = 0; i < RAM_DEPTH; i = i + 1)
                BRAM[i] = {RAM_WIDTH{1'b0}};
        end
    endgenerate

    reg [RAM_WIDTH-1:0] BRAM [RAM_DEPTH-1:0];
    reg [RAM_WIDTH-1:0] ram_data_a = {RAM_WIDTH{1'b0}};
    reg [RAM_WIDTH-1:0] ram_data_b = {RAM_WIDTH{1'b0}};

    always @(posedge clka) begin
        if (wea) BRAM[addra] <= dina;
        ram_data_a <= BRAM[addra];
    end

    always @(posedge clkb) begin
        if (web) BRAM[addrb] <= dinb;
        ram_data_b <= BRAM[addrb];
    end

    // Add a 2 clock cycle read latency to improve clock-to-out timing
    reg [RAM_WIDTH-1:0] douta_reg = {RAM_WIDTH{1'b0}};
    reg [RAM_WIDTH-1:0] doutb_reg = {RAM_WIDTH{1'b0}};

    always @(posedge clka) douta_reg <= ram_data_a;
    always @(posedge clkb) doutb_reg <= ram_data_b;

    assign douta = douta_reg;
    assign doutb = doutb_reg;
endmodule
module trigger_block (
    input wire clk,

    // probes
    input wire larry,
    input wire curly,
    input wire moe,
    input wire [3:0] shemp,

    // trigger
    output reg trig,

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
    localparam MAX_ADDR = 7;

    // trigger configuration registers
    // - each probe gets an operation and a compare register
    // - at the end we OR them all together. along with any custom probes the user specs

    reg [3:0] larry_op = 0;
    reg larry_arg = 0;
    reg larry_trig;
    
    trigger #(.INPUT_WIDTH(1)) larry_trigger (
        .clk(clk),
    
        .probe(larry),
        .op(larry_op),
        .arg(larry_arg),
        .trig(larry_trig));
    reg [3:0] curly_op = 0;
    reg curly_arg = 0;
    reg curly_trig;
    
    trigger #(.INPUT_WIDTH(1)) curly_trigger (
        .clk(clk),
    
        .probe(curly),
        .op(curly_op),
        .arg(curly_arg),
        .trig(curly_trig));
    reg [3:0] moe_op = 0;
    reg moe_arg = 0;
    reg moe_trig;
    
    trigger #(.INPUT_WIDTH(1)) moe_trigger (
        .clk(clk),
    
        .probe(moe),
        .op(moe_op),
        .arg(moe_arg),
        .trig(moe_trig));
    reg [3:0] shemp_op = 0;
    reg [3:0] shemp_arg = 0;
    reg shemp_trig;
    
    trigger #(.INPUT_WIDTH(4)) shemp_trigger (
        .clk(clk),
    
        .probe(shemp),
        .op(shemp_op),
        .arg(shemp_arg),
        .trig(shemp_trig));

   assign trig = larry_trig || curly_trig || moe_trig || shemp_trig;

    // perform register operations
    always @(posedge clk) begin
        addr_o <= addr_i;
        wdata_o <= wdata_i;
        rdata_o <= rdata_i;
        rw_o <= rw_i;
        valid_o <= valid_i;
        rdata_o <= rdata_i;

        if( (addr_i >= BASE_ADDR) && (addr_i <= BASE_ADDR + MAX_ADDR) ) begin

            // reads
            if(valid_i && !rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: rdata_o <= larry_op;
                    BASE_ADDR + 1: rdata_o <= larry_arg;
                    BASE_ADDR + 2: rdata_o <= curly_op;
                    BASE_ADDR + 3: rdata_o <= curly_arg;
                    BASE_ADDR + 4: rdata_o <= moe_op;
                    BASE_ADDR + 5: rdata_o <= moe_arg;
                    BASE_ADDR + 6: rdata_o <= shemp_op;
                    BASE_ADDR + 7: rdata_o <= shemp_arg;
                endcase
            end

            // writes
            else if(valid_i && rw_i) begin
                case (addr_i)
                    BASE_ADDR + 0: larry_op <= wdata_i;
                    BASE_ADDR + 1: larry_arg <= wdata_i;
                    BASE_ADDR + 2: curly_op <= wdata_i;
                    BASE_ADDR + 3: curly_arg <= wdata_i;
                    BASE_ADDR + 4: moe_op <= wdata_i;
                    BASE_ADDR + 5: moe_arg <= wdata_i;
                    BASE_ADDR + 6: shemp_op <= wdata_i;
                    BASE_ADDR + 7: shemp_arg <= wdata_i;
                endcase
            end
        end
    end
endmodule
module trigger (
    input wire clk,

    input wire [INPUT_WIDTH-1:0] probe,
    input wire [3:0] op,
    input wire [INPUT_WIDTH-1:0] arg,

    output reg trig);

    parameter INPUT_WIDTH = 0;

    localparam DISABLE = 0;
    localparam RISING = 1;
    localparam FALLING = 2;
    localparam CHANGING = 3;
    localparam GT = 4;
    localparam LT = 5;
    localparam GEQ = 6;
    localparam LEQ = 7;
    localparam EQ = 8;
    localparam NEQ = 9;

    reg [INPUT_WIDTH-1:0] probe_prev = 0;
    always @(posedge clk) probe_prev <= probe;

    always @(*) begin
        case (op)
            RISING :    trig = (probe > probe_prev);
            FALLING :   trig = (probe < probe_prev);
            CHANGING :  trig = (probe != probe_prev);
            GT:         trig = (probe > arg);
            LT:         trig = (probe < arg);
            GEQ:        trig = (probe >= arg);
            LEQ:        trig = (probe <= arg);
            EQ:         trig = (probe == arg);
            NEQ:        trig = (probe != arg);
            default:    trig = 0;
        endcase
    end
endmodule
