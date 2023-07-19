block_memory #(
    .WIDTH(/* WIDTH */),
    .DEPTH(/* DEPTH */)
) /* INST_NAME */ (
    .clk(clk),

    .addr_i(),
    .data_i(),
    .rw_i(),
    .valid_i(),

    .user_clk(/* INST_NAME */_clk),
    .user_addr(/* INST_NAME */_addr),
    .user_din(/* INST_NAME */_din),
    .user_dout(/* INST_NAME */_dout),
    .user_we(/* INST_NAME */_we),

    .addr_o(),
    .data_o(),
    .rw_o(),
    .valid_o());