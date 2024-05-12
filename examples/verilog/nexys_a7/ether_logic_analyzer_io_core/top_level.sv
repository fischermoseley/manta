module top_level (
    input wire clk_100mhz,
    output logic eth_refclk,
    input wire btnc,

    output logic [15:0] led,
    input wire [15:0] sw,

    input wire eth_crsdv,
    output logic eth_mdc,
    output logic eth_mdio,
    output logic eth_rstn,
    input wire [1:0] eth_rxd,
    output logic [1:0] eth_txd,
    output logic eth_txen
);

logic ethclk;
assign eth_refclk = ethclk;
divider div (.clk(clk_100mhz), .ethclk(ethclk));

    logic probe0;
    logic [3:0] probe1;
    logic [7:0] probe2;
    logic [15:0] probe3;

    always @(posedge ethclk) begin
        probe0 <= probe0 + 1;
        probe1 <= probe1 + 1;
        probe2 <= probe2 + 1;
        probe3 <= probe3 + 1;
    end

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

    .probe0(probe0),
    .probe1(probe1),
    .probe2(probe2),
    .probe3(probe3),

    .led(led),
    .sw(sw));

endmodule