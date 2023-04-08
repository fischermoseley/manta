rx_uart #(.CLOCKS_PER_BAUD(/* CLOCKS_PER_BAUD */)) urx (
    .i_clk(clk),
    .i_uart_rx(rx),
    .o_wr(urx_brx_axiv),
    .o_data(urx_brx_axid));

logic [7:0] urx_brx_axid;
logic urx_brx_axiv;

bridge_rx brx (
    .clk(clk),

    .rx_data(urx_brx_axid),
    .rx_valid(urx_brx_axiv),

    .addr_o(),
    .wdata_o(),
    .rw_o(),
    .valid_o());