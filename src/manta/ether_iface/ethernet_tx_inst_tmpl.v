ethernet_tx #(
    .FPGA_MAC(/* FPGA_MAC */),
    .HOST_MAC(/* HOST_MAC */),
    .ETHERTYPE(/* ETHERTYPE */)
) etx (
    .clk(clk),

    .rdata_i(),
    .rw_i(),
    .valid_i(),

    .txen(txen),
    .txd(txd));