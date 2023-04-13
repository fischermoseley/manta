
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
