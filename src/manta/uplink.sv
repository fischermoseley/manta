`default_nettype none

`define IDLE 0
`define RUN 1

module uplink(
    input wire clk,
    input wire rst,
    input wire start,
    output wire busy,
    
    /* Begin autogenerated probe definitions */
    output wire alice,
    output wire [2:0] bob,
    output wire charlotte,
    output wire [3:0] donovan
    /* End autogenerated probe definitions */
    );

    /*
    this works in a very simple way - all it does is chill
    in the idle state, until a request to start uplinking is
    received. when that happens, it'll start dumping things
    from the port until the BRAM is empty, and then that's it.

    this dumping happens with the trigger condition - the clock
    cycle that the triggr goes high on, we should output data.
    or have the option to, with some kind of holdoff. 

    oh wait this might be a little hard since we've got the two
    clock cycles of latency on the BRAM, so we actually need to 
    preload the first two values of the bram into registers so
    when it's time to go

    actually it's probably worth thinking more about how useful
    this would acatully be, because right now i'm not seeing too
    many situations where i'd want to use this. and we can always
    come back to it
    */

    parameter WIDTH = 0;
    parameter DEPTH = 0;
    localparam AW = $clog2(DEPTH);

    logic [AW:0] read_pointer;
    logic state;

    always_ff @(posedge clk) begin
        if(rst) begin
            state <= `IDLE
            read_pointer <= 0;
        end

        else begin
            if(state == `IDLE) begin
                // do nothing, just wait for trigger condition
                if(start) state <= `RUN;
            end

            if(state == `RUN) begin
                
            end
        end
    end

    xilinx_true_dual_port_read_first_2_clock_ram #(
        .RAM_WIDTH(),
        .RAM_DEPTH(),
        .RAM_PERFORMANCE("HIGH PERFORMANCE")
        
        ) buffer (
        
        // write port (currently unused)
		.clka(clk),
		.rsta(rst),
		.ena(1),
		.addra(0),
		.dina(0),
		.wea(0),
		.regcea(1),
		.douta(),

		// read port
		.clkb(clk),
		.rstb(rst),
		.enb(1),
		.addrb(read_pointer),
		.dinb(),
		.web(0),
		.regceb(1),
		.doutb(data_out));


endmodule

`default_nettype wire