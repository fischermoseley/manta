module seven_segment_controller #(parameter COUNT_TO = 100000)
                                (    input wire         clk_in,
                                    input wire         rst_in,
                                    input wire [31:0]  val_in,
                                    output logic[6:0]   cat_out,
                                    output logic[7:0]   an_out
                                 );

  logic[7:0]      segment_state;
  logic[31:0]     segment_counter;
  logic [3:0]     routed_vals;
  logic [6:0]     led_out;

  bto7s mbto7s (.x_in(routed_vals), .s_out(led_out));

  assign cat_out = ~led_out;
  assign an_out = ~segment_state;

  always_comb begin
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
  always_ff @(posedge clk_in)begin
    if (rst_in)begin
      segment_state <= 8'b0000_0001;
      segment_counter <= 32'b0;
    end else begin
      if (segment_counter == COUNT_TO)begin
          segment_counter <= 32'd0;
          segment_state <= {segment_state[6:0],segment_state[7]};
      end else begin
          segment_counter <= segment_counter +1;
      end
    end
  end
endmodule //seven_segment_controller
