bridge_tx btx (
    .clk(clk),

    .data_i(),
    .rw_i(),
    .valid_i(),

    .data_o(btx_utx_data),
    .start_o(btx_utx_start),
    .done_i(utx_btx_done));

reg [7:0] btx_utx_data;
reg btx_utx_start;
reg utx_btx_done;

uart_tx #(.CLOCKS_PER_BAUD(/* CLOCKS_PER_BAUD */)) utx (
    .clk(clk),

    .data_i(btx_utx_data),
    .start_i(btx_utx_start),
    .done_o(utx_btx_done),

    .tx(tx));