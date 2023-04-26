bridge_tx btx (
    .clk(clk),

    .rdata_i(),
    .rw_i(),
    .valid_i(),

    .ready_i(utx_btx_ready),
    .data_o(btx_utx_data),
    .valid_o(btx_utx_valid));

logic utx_btx_ready;
logic btx_utx_valid;
logic [7:0] btx_utx_data;

uart_tx #(.CLOCKS_PER_BAUD(/* CLOCKS_PER_BAUD */)) utx (
    .clk(clk),

    .data(btx_utx_data),
    .valid(btx_utx_valid),
    .ready(utx_btx_ready),

    .tx(tx));