`default_nettype none
`timescale 1ns/1ps

module ssd (
    input wire clk,
    input wire [31:0] val,
    output reg [6:0] cat,
    output reg [7:0] an);

    parameter COUNT_TO = 100000;

    reg [7:0] segment_state = 8'b0000_0001;
    reg [31:0] segment_counter = 32'b0;
    reg [3:0] digit;
    reg [6:0] led_out;

    bto7s mbto7s (
        .x_in(digit),
        .s_out(led_out));

    assign cat = ~led_out;
    assign an = ~segment_state;

    always @(*) begin
        case(segment_state)
            8'b0000_0001:   digit = val[3:0];
            8'b0000_0010:   digit = val[7:4];
            8'b0000_0100:   digit = val[11:8];
            8'b0000_1000:   digit = val[15:12];
            8'b0001_0000:   digit = val[19:16];
            8'b0010_0000:   digit = val[23:20];
            8'b0100_0000:   digit = val[27:24];
            8'b1000_0000:   digit = val[31:28];
            default:        digit = val[3:0];
        endcase
    end

    always @(posedge clk) begin
        segment_counter <= segment_counter + 1;

        if (segment_counter == COUNT_TO) begin
            segment_counter <= 32'd0;
            segment_state <= {segment_state[6:0], segment_state[7]};
        end
    end
endmodule

module bto7s (
    input wire [3:0] x_in,
    output reg [6:0] s_out);

    reg sa, sb, sc, sd, se, sf, sg;
    assign s_out = {sg, sf, se, sd, sc, sb, sa};

    // array of bits that are "one hot" with numbers 0 through 15
    reg [15:0] num;
    genvar i;
    generate
        for(i=0; i<16; i=i+1)
            assign num[i] = (x_in == i);
    endgenerate

    // map one-hot bits to active segments
    assign sa = (num & 16'b1101_0111_1110_1101) > 0;
    assign sb = (num & 16'b0010_0111_1001_1111) > 0;
    assign sc = (num & 16'b0010_1111_1111_1011) > 0;
    assign sd = (num & 16'b0111_1011_0110_1101) > 0;
    assign se = (num & 16'b1111_1101_0100_0101) > 0;
    assign sf = (num & 16'b1101_1111_0111_0001) > 0;
    assign sg = (num & 16'b1110_1111_0111_1100) > 0;
endmodule

`default_nettype wire