module top_level (
    input wire clk_100mhz,
    input wire btnc,

    // VGA I/O
    output logic [3:0] vga_r,
    output logic [3:0] vga_g,
    output logic [3:0] vga_b,
    output logic vga_hs,
    output logic vga_vs,

    // Ethernet I/O
    output logic eth_refclk,
    input wire eth_crsdv,
    output logic eth_mdc,
    output logic eth_mdio,
    output logic eth_rstn,
    input wire [1:0] eth_rxd,
    output logic [1:0] eth_txd,
    output logic eth_txen);

    logic ethclk;
    logic clk_65mhz;
    assign eth_refclk = ethclk;
    divider div (.clk_100mhz(clk_100mhz), .clk_50mhz(ethclk), .clk_65mhz(clk_65mhz));

    logic [11:0] user_data_out;
    logic [13:0] user_addr;

    manta manta_inst(
        .clk(ethclk),
        .rst(btnc),
        .rmii_clocks_ref_clk(ethclk),
        .rmii_crs_dv(eth_crsdv),
        .rmii_mdc(eth_mdc),
        .rmii_mdio(eth_mdio),
        .rmii_rst_n(eth_rstn),
        .rmii_rx_data(eth_rxd),
        .rmii_tx_data(eth_txd),
        .rmii_tx_en(eth_txen),

        .user_addr(user_addr),
        .user_data_out(user_data_out),
        .user_clk(clk_65mhz));


    logic [10:0] hcount;
    logic [9:0] vcount;
    logic hsync, vsync, blank;

    vga vga_gen(
        .pixel_clk_in(clk_65mhz),
        .hcount_out(hcount),
        .vcount_out(vcount),
        .hsync_out(hsync),
        .vsync_out(vsync),
        .blank_out(blank));

    // calculate ROM address
    parameter WIDTH = 128;
    parameter HEIGHT = 128;

    assign user_addr = hcount + (vcount * WIDTH);

    logic in_sprite;
    assign in_sprite = ((hcount < WIDTH) && (vcount < HEIGHT));

    logic [11:0] color;
    // assign color = in_sprite ? user_data_out : 0;
    // assign color = 12'b1111_0000_1111;
    assign color = user_data_out;

    // the following lines are required for the Nexys4 VGA circuit - do not change
    assign vga_r = ~blank ? color[11:8]: 0;
    assign vga_g = ~blank ? color[7:4] : 0;
    assign vga_b = ~blank ? color[3:0] : 0;

    assign vga_hs = ~hsync;
    assign vga_vs = ~vsync;

endmodule