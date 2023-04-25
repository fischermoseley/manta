`default_nettype none
`timescale 1ns/1ps

module mac_tb();
    logic clk;

    always begin
        #5;
        clk = !clk;
    end

    logic crsdv;
    logic [1:0] rxd;

    logic txen;
    logic [1:0] txd;

    logic [15:0] mtx_data;
    logic [15:0] mtx_ethertype;
    logic mtx_start;

    logic [15:0] mrx_data;
    logic [15:0] mrx_ethertype;
    logic mrx_valid;

    mac_tx mtx (
        .clk(clk),

        .data(mtx_data),
        .ethertype(mtx_ethertype),
        .start(mtx_start),

        .txen(txen),
        .txd(txd));

    assign rxd = txd;
    assign crsdv = txen;

    mac_rx mrx (
        .clk(clk),

        .crsdv(crsdv),
        .rxd(rxd),

        .data(mrx_data),
        .ethertype(mrx_ethertype),
        .valid(mrx_valid));

    initial begin
        $dumpfile("mac_tb.vcd");
        $dumpvars(0, mac_tb);
        clk = 0;
        mtx_ethertype = 0;
        mtx_data = 0;
        mtx_start = 0;
        #10;

        for (int i=0; i<128; i=i+1) begin
            mtx_data = i;
            mtx_ethertype = i;
            mtx_start = 0;
            #10;
            mtx_start = 1;
            #10;
            mtx_start = 0;
            while(!mrx_valid) #10;

            #1000;

            assert(mrx_data == i) else $error("data mismatch!");
        end
        $finish();
    end

endmodule
`default_nettype wire