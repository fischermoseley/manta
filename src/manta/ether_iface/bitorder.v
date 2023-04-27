`default_nettype none
`timescale 1ns / 1ps

`define BO_SENDA	2'b00
`define BO_SENDB	2'b01
`define BO_EMPTYA	2'b10
`define BO_EMPTYB	2'b11

module bitorder (
	input wire clk,

	input wire axiiv,
    input wire [1:0] axiid,

    output reg [1:0] axiod,
    output reg axiov);

	/* Two registers to hold data coming in off the wire,
	 * byte by byte. This is where we'll buffer until
	 * we've received a byte of data, at which point
	 * we'll start sending out the byte in the correct
	 * order using one register. Meanwhile, we'll start
	 * receiving into the other register - dual buffers.
	 */
	reg [7:0] bufa = 8'b0;
    reg [7:0] bufb = 8'b0;

	/* A counter. This indicates what 'stage' we're in,
	 * and always refers to the index we're reading into
	 * in the receiving buffer or sending out of in the
 	 * sending buffer
	 */
	reg [2:0] countera = 3'b0;
    reg [2:0] counterb = 3'b0;

	/* Which state we're in - should we be using buffer
	 * A to send, buffer B to send, or neither because
	 * we've just come out of reset?
	 */
	reg [1:0] state = `BO_EMPTYB;
	initial axiov = 0;
	initial axiod = 0;

	always @(*) begin: AXIOV
		if (state == `BO_SENDA || state == `BO_SENDB) axiov = 1'b1;
		else axiov = 1'b0;
	end

	always @(*) begin: AXIOD
		if (state == `BO_SENDA) axiod = bufa[countera +: 2];
		else if (state == `BO_SENDB) axiod = bufb[counterb +: 2];
		else axiod = 1'b0;
	end

	always @(posedge clk) begin: BUFFERIN
        if (axiiv) begin
			case (state)
				`BO_EMPTYB, `BO_SENDB:
					bufa[countera +: 2] <= axiid;
				`BO_EMPTYA, `BO_SENDA:
					bufb[counterb +: 2] <= axiid;
			endcase
		end

        else if (state == `BO_EMPTYB || state == `BO_EMPTYA) begin
			bufa <= 8'b0;
			bufb <= 8'b0;
		end
	end

	always @(posedge clk) begin: STATES
        case (state)
            `BO_EMPTYB: begin
                if (axiiv) begin
                    if (countera == 3'h6)
                        state <= `BO_SENDA;
                    else countera <= countera + 2;
                end else countera <= 3'b0;
            end

            `BO_EMPTYA: begin
                if (axiiv) begin
                    if (counterb == 3'h6)
                        state <= `BO_SENDB;
                    else counterb <= counterb + 2;
                end else counterb <= 3'b0;
            end

            `BO_SENDB: begin
                if (counterb == 3'h0) state <= `BO_EMPTYB;
                else counterb <= counterb - 2;

                if (axiiv) begin
                    if (countera == 3'h6)
                        state <= `BO_SENDA;
                    else countera <= countera + 2;
                end
            end

            `BO_SENDA: begin
                if (countera == 3'h0) state <= `BO_EMPTYA;
                else countera <= countera - 2;

                if (axiiv) begin
                    if (counterb == 3'h6)
                        state <= `BO_SENDB;
                    else counterb <= counterb + 2;
                end
            end
        endcase
	end
endmodule

`default_nettype wire
