uart_rx #(.CLOCKS_PER_BAUD(/* CLOCKS_PER_BAUD */)) urx (
    .clk(clk),
    .rx(rx),

    .data_o(urx_brx_data),
    .valid_o(urx_brx_valid));

reg [7:0] urx_brx_data;
reg urx_brx_valid;

bridge_rx brx (
    .clk(clk),

    .data_i(urx_brx_data),
    .valid_i(urx_brx_valid),

    .addr_o(),
    .data_o(),
    .rw_o(),
    .valid_o());