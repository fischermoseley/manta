/*
This playback module was generated with Manta /* VERSION */ on /* TIMESTAMP */ by /* USER */

If this breaks or if you've got dank formal verification memes, contact fischerm [at] mit.edu

Provided under a GNU GPLv3 license. Go wild.

Here's an example instantiation of the Manta module you configured, feel free to copy-paste
this into your source!

/* MODULE_NAME */ #(.MEM_FILE("capture.mem")) /* MODULE_NAME */_inst (
    .clk(clk),
    .enable(1'b1),

    /* PORTS */);

*/


module /* MODULE_NAME */ (
    input wire clk,

    input wire enable,
    output reg done,

    /* PROBE_DEC */);

    parameter MEM_FILE = "";
    localparam SAMPLE_DEPTH = /* SAMPLE_DEPTH */;
    localparam TOTAL_PROBE_WIDTH = /* TOTAL_PROBE_WIDTH */;

    reg [TOTAL_PROBE_WIDTH-1:0] capture [SAMPLE_DEPTH-1:0];
    reg [$clog2(SAMPLE_DEPTH)-1:0] addr;
    reg [TOTAL_PROBE_WIDTH-1:0] sample;

    assign done = (addr >= SAMPLE_DEPTH);

    initial begin
        $readmemb(MEM_FILE, capture, 0, SAMPLE_DEPTH-1);
        addr = 0;
    end

    always @(posedge clk) begin
        if (enable && !done) begin
            addr = addr + 1;
            sample = capture[addr];
            /* PROBES_CONCAT */ = sample;
        end
    end
endmodule