`default_nettype none
`timescale 1ns/1ps

module mac_rx (
    input wire clk,

    input wire crsdv,
    input wire [1:0] rxd,

    output reg [55:0] payload,
    output reg valid);

    parameter FPGA_MAC = 0;
    parameter ETHERTYPE = 0;

	reg [1:0] ether_axiod;
	reg ether_axiov;

	ether e (
        .clk(clk),
		.rxd(rxd),
		.crsdv(crsdv),
		.axiov(ether_axiov),
		.axiod(ether_axiod));

	reg [1:0] bitorder_axiod;
	reg bitorder_axiov;

	bitorder b (
        .clk(clk),
        .axiiv(ether_axiov),
        .axiid(ether_axiod),
        .axiov(bitorder_axiov),
        .axiod(bitorder_axiod));

	reg [1:0] firewall_axiod;
	reg firewall_axiov;

	firewall #(
        .FPGA_MAC(FPGA_MAC),
        .ETHERTYPE(ETHERTYPE)
    ) f (
        .clk(clk),
        .axiiv(bitorder_axiov),
        .axiid(bitorder_axiod),
        .axiov(firewall_axiov),
        .axiod(firewall_axiod));

	reg [55:0] aggregate_axiod;
	reg aggregate_axiov;

	aggregate a (
        .clk(clk),
        .axiiv(firewall_axiov),
        .axiid(firewall_axiod),
        .axiov(aggregate_axiov),
        .axiod(aggregate_axiod));

	reg cksum_done;
    reg cksum_kill;

	cksum c (
        .clk(clk),
		.axiiv(ether_axiov),
		.axiid(ether_axiod),
		.done(cksum_done),
		.kill(cksum_kill));

    // state machine
    localparam IDLE = 0;
    localparam WAIT_FOR_DATA = 1;
    localparam WAIT_FOR_FCS = 2;

    reg [1:0] state = IDLE;

    initial valid = 0;
    initial payload = 0;

    always @(posedge clk) begin
        valid <= 0;

        if(state == IDLE) begin
            if(crsdv) state <= WAIT_FOR_DATA;
        end

        else if(state == WAIT_FOR_DATA) begin
            if(aggregate_axiov) begin
                state <= WAIT_FOR_FCS;
                payload <= aggregate_axiod;
            end

            // if aggregate never gives us data,
            // go back to idle when the packet ends
            else if(cksum_done) state <= IDLE;
        end

        else if(state == WAIT_FOR_FCS) begin
            if(cksum_done) begin
                state <= IDLE;
                valid <= ~cksum_kill;
            end
        end
    end
endmodule

`default_nettype wire