`default_nettype none
`timescale 1ns/1ps

module mac_tx (
    input wire clk,

    input wire [(8 * PAYLOAD_LENGTH_BYTES)-1:0] payload,
    input wire start,

    output reg txen,
    output reg [1:0] txd);

    // packet magic numbers
    localparam PREAMBLE = {7{8'b01010101}};
    localparam SFD = 8'b11010101;
    parameter [47:0] SRC_MAC = 0;
    parameter [47:0] DST_MAC = 0;
    parameter [15:0] ETHERTYPE = 0;
    parameter PAYLOAD_LENGTH_BYTES = 0;

    // all lengths are in units of dibits, hence all the mulitplies by four
    localparam PREAMBLE_LEN = 7 * 4;
    localparam SFD_LEN = 1 * 4;
    localparam SRC_MAC_LEN = 6 * 4;
    localparam DST_MAC_LEN = 6 * 4;
    localparam ETHERTYPE_LEN = 2 * 4;
    localparam PAYLOAD_LEN = PAYLOAD_LENGTH_BYTES * 4;
    localparam ZERO_PAD_LEN = (46 * 4) - PAYLOAD_LEN + 4; // minimum payload size is 46 bytes
    localparam FCS_LEN = 4 * 4;
    localparam IPG_LEN = 96 / 2;

    reg [1:0] bitorder_axiid;
    reg [1:0] bitorder_axiod;
    reg bitorder_axiiv;
    reg bitorder_axiov;

    bitorder bitorder (
        .clk(clk),

        .axiiv(bitorder_axiiv),
        .axiid(bitorder_axiid),

        .axiov(bitorder_axiov),
        .axiod(bitorder_axiod));

    reg crc_rst = 1;
    reg crc_axiiv = 0;
    reg [31:0] crc_axiod;

    crc32 crc (
        .clk(clk),
        .rst(crc_rst),

        .axiiv(crc_axiiv),
        .axiid(bitorder_axiod),

        // TODO: remove axiov from crc32 module, it's always valid
        .axiov(),
        .axiod(crc_axiod));


    // state machine
    reg [8:0] counter = 0;
    reg [3:0] state = 0;

    localparam IDLE_STATE = 0;
    localparam PREAMBLE_STATE = 1;
    localparam SFD_STATE = 2;
    localparam DST_MAC_STATE = 3;
    localparam SRC_MAC_STATE = 4;
    localparam ETHERTYPE_STATE = 5;
    localparam PAYLOAD_STATE = 6;
    localparam ZERO_PAD_STATE = 7;
    localparam FCS_STATE = 8;
    localparam IPG_STATE = 9;


    // sequential logic manages the state machine
    always @(posedge clk) begin
        counter <= counter + 1;
        crc_rst <= 0;

        if(state == IDLE_STATE) begin
            counter <= 0;
            crc_axiiv <= 0;
            if(start) state <= PREAMBLE_STATE;
        end

        else if(state == PREAMBLE_STATE) begin
            if(counter == PREAMBLE_LEN - 1) begin
                counter <= 0;
                state <= SFD_STATE;
            end
        end

        else if(state == SFD_STATE) begin
            if(counter == SFD_LEN - 1) begin
                counter <= 0;
                state <= DST_MAC_STATE;
            end
        end

        else if(state == DST_MAC_STATE) begin
            // this is because the crc module lags behind the FSM,
            // as it has to go through bitorder first
            if(counter == 3) crc_axiiv <= 1;

            if(counter == DST_MAC_LEN - 1) begin
                counter <= 0;
                state <= SRC_MAC_STATE;
            end
        end

        else if(state == SRC_MAC_STATE) begin
            if(counter == SRC_MAC_LEN - 1) begin
                counter <= 0;
                state <= ETHERTYPE_STATE;
            end
        end

        else if(state == ETHERTYPE_STATE) begin
            if(counter == ETHERTYPE_LEN - 1) begin
                counter <= 0;
                state <= PAYLOAD_STATE;
            end
        end

        else if(state == PAYLOAD_STATE) begin
            if(counter == PAYLOAD_LEN - 1) begin
                counter <= 0;
                state <= ZERO_PAD_STATE;
            end
        end

        else if(state == ZERO_PAD_STATE) begin
            if(counter == ZERO_PAD_LEN - 1) begin
                crc_axiiv <= 0;
                counter <= 0;
                state <= FCS_STATE;
            end
        end

        else if(state == FCS_STATE) begin
            if(counter == FCS_LEN - 1) begin
                counter <= 0;
                state <= IPG_STATE;
            end
        end

        else if(state == IPG_STATE) begin
            if(counter == IPG_LEN - 1) begin
                crc_rst <= 1;
                counter <= 0;
                state <= IDLE_STATE;
            end
        end
    end

    // combinational logic handles the pipeline
    always @(*) begin
        case (state)
            IDLE_STATE: begin
                bitorder_axiiv = 0;
                bitorder_axiid = 0;
                txen = 0;
                txd = 0;
            end

            PREAMBLE_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = PREAMBLE[2*(PREAMBLE_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            SFD_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = SFD[2*(SFD_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            DST_MAC_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = DST_MAC[2*(DST_MAC_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            SRC_MAC_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = SRC_MAC[2*(SRC_MAC_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            ETHERTYPE_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = ETHERTYPE[2*(ETHERTYPE_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            PAYLOAD_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = payload[2*(PAYLOAD_LEN-counter)-1-:2];
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            ZERO_PAD_STATE: begin
                bitorder_axiiv = 1;
                bitorder_axiid = 0;
                txen = bitorder_axiov;
                txd = bitorder_axiod;
            end

            FCS_STATE: begin
                bitorder_axiiv = 0;
                bitorder_axiid = 0;
                txen = 1;
                txd = {crc_axiod[2*(FCS_LEN-counter)-2], crc_axiod[2*(FCS_LEN-counter)-1]};
            end

            IPG_STATE: begin
                bitorder_axiiv = 0;
                bitorder_axiid = 0;
                txen = 0;
                txd = 0;
            end

            default: begin
                bitorder_axiiv = 0;
                bitorder_axiid = 0;
                txen = 0;
                txd = 0;
            end
        endcase
    end
endmodule

`default_nettype wire