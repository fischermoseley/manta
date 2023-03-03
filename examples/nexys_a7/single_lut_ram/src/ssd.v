module ssd(
    input wire         clk_in,
    input wire         rst_in,
    input wire [31:0]  val_in,
    output reg[6:0]   cat_out,
    output reg[7:0]   an_out);

    parameter COUNT_TO = 100000; 
    logic[7:0]      segment_state;
    logic[31:0]     segment_counter;
    logic [3:0]     routed_vals;
    logic [6:0]     led_out;

    bto7s mbto7s (.x_in(routed_vals), .s_out(led_out));

    assign cat_out = ~led_out;
    assign an_out = ~segment_state;

    always @(*) begin
        case(segment_state)
            8'b0000_0001:   routed_vals = val_in[3:0];
            8'b0000_0010:   routed_vals = val_in[7:4];
            8'b0000_0100:   routed_vals = val_in[11:8];
            8'b0000_1000:   routed_vals = val_in[15:12];
            8'b0001_0000:   routed_vals = val_in[19:16];
            8'b0010_0000:   routed_vals = val_in[23:20];
            8'b0100_0000:   routed_vals = val_in[27:24];
            8'b1000_0000:   routed_vals = val_in[31:28];
            default:        routed_vals = val_in[3:0];
        endcase
    end

    always @(posedge clk_in) begin
        if (rst_in) begin
            segment_state <= 8'b0000_0001;
            segment_counter <= 32'b0;
        end 
        
        else begin
            if (segment_counter == COUNT_TO) begin
                segment_counter <= 32'd0;
                segment_state <= {segment_state[6:0],segment_state[7]};
            end else begin
                segment_counter <= segment_counter +1;
            end
        end
    end
endmodule


module bto7s(
    input wire [3:0] x_in,
    output reg [6:0] s_out);

    reg sa, sb, sc, sd, se, sf, sg;
    assign s_out = {sg, sf, se, sd, sc, sb, sa};

    // array of bits that are "one hot" with numbers 0 through 15
    reg [15:0] num;

    assign num[0] = ~x_in[3] && ~x_in[2] && ~x_in[1] && ~x_in[0];
    assign num[1] = ~x_in[3] && ~x_in[2] && ~x_in[1] && x_in[0];
    assign num[2] = x_in == 4'd2;
    assign num[3] = x_in == 4'd3;
    assign num[4] = x_in == 4'd4;
    assign num[5] = x_in == 4'd5;
    assign num[6] = x_in == 4'd6;
    assign num[7] = x_in == 4'd7;
    assign num[8] = x_in == 4'd8;
    assign num[9] = x_in == 4'd9;
    assign num[10] = x_in == 4'd10;
    assign num[11] = x_in == 4'd11;
    assign num[12] = x_in == 4'd12;
    assign num[13] = x_in == 4'd13;
    assign num[14] = x_in == 4'd14;
    assign num[15] = x_in == 4'd15;

    assign sa = num[0] || num[2] || num[3] || num[5] || num[6] || num[7] || num[8] || num[9] || num[10] || num[12] ||num[14] ||num[15];
    assign sb = num[0] || num[1] || num[2] || num[3] || num[4] || num[7] || num[8] || num[9] || num[10] || num[13];
    assign sc = num[0] || num[1] || num[3] || num[4] || num[5] || num[6] || num[7] || num[8] || num[9] || num[10] || num[11] || num[13];
    assign sd = num[0] || num[2] || num[3] || num[5] || num[6] || num[8] || num[9] || num[11] || num[12] || num[13] || num[14];
    assign se = num[0] || num[2] || num[6] || num[8] || num[10] || num[11] || num[12] || num[13] || num[14] || num[15];
    assign sf = num[0] || num[4] || num[5] || num[6] || num[8] || num[9] || num[10] || num[11] || num[12] || num[14] || num[15];
    assign sg = num[2] || num[3] || num[4] || num[5] || num[6] || num[8] || num[9] || num[10] || num[11] || num[13] || num[14] ||num[15];
endmodule
