`define CP	20
`define HCP	(`CP / 2)

/* checking helper for testing tasks */
`define CHECK(COND, TESTOK, MSG) do begin	\
	if (!(COND) && TESTOK) begin		\
		$display("FAIL: %s", MSG);	\
		TESTOK = 0;			\
	end					\
end while (0)

`default_nettype none
`timescale 1ns / 1ps

`define PREAM_BAD	2'b10
`define PREAM_FIRST	2'b00
`define CRSDV_HOLD	10

`define MAC_BITS	48
`define ETYPE_BITS	16
`define MAX_MSG_BITS	128

`define AGGREGATE_SIZE	32
`define TIMEOUT		200

`define PREAMBLE	64'h5555_5555_5555_5557	/* pre-flipped for us */
`define MAC_BCAST	48'hFF_FF_FF_FF_FF_FF
`define MAC_SRC		48'h69_69_69_69_69_69	/* don't care if flipped */
`define ETYPE		16'h6969		/* don't care if flipped */

`define MSG(BITS, SIZE)	(BITS << (`MAX_MSG_BITS - SIZE))

`define TTINY		`MSG(2'b10, 2)
`define T32		`MSG(32'h4353_f92c, 32)
`define T64		`MSG(64'h1234_5678_0000_0000, 64)
`define T128		`MSG({(64){2'b10}}, 128)

`define T64_EXPECT	32'h84_1C_95_2D
`define T128_EXPECT	32'hAA_AA_AA_AA

module integrationsim;

	logic clk, rst;

	logic[1:0] rxd;
	logic crsdv;

	/* ether -> bitorder */
	logic[1:0] ether_axiod;
	logic ether_axiov;

	/* bitorder -> firewall */
	logic[1:0] bitorder_axiod;
	logic bitorder_axiov;

	/* firewall -> aggregate */
	logic[1:0] firewall_axiod;
	logic firewall_axiov;

	/* aggregate output */
	logic[31:0] axiod;
	logic axiov;

	/* constants */
	logic[0:63] preamble;
	logic[0:`MAC_BITS-1] dst, src;
	logic[0:`ETYPE_BITS-1] etype;

	assign preamble = `PREAMBLE;
	assign dst = `MAC_BCAST;
	assign src = `MAC_SRC;
	assign etype = `ETYPE;

	ether e(.clk(clk),
		.rst(rst),
		.rxd(rxd),
		.crsdv(crsdv),
		.axiov(ether_axiov),
		.axiod(ether_axiod));

	bitorder b(.clk(clk),
		   .rst(rst),
		   .axiiv(ether_axiov),
		   .axiid(ether_axiod),
		   .axiov(bitorder_axiov),
		   .axiod(bitorder_axiod));

	firewall f(.clk(clk),
		   .rst(rst),
		   .axiiv(bitorder_axiov),
		   .axiid(bitorder_axiod),
		   .axiov(firewall_axiov),
		   .axiod(firewall_axiod));

	aggregate a(.clk(clk),
		    .rst(rst),
		    .axiiv(firewall_axiov),
		    .axiid(firewall_axiod),
		    .axiov(axiov),
		    .axiod(axiod));

	integer ok;

	task test;
		input[0:`MAX_MSG_BITS-1] msg;
		input[63:0] msgsize;
		input[31:0] exp;
		input showexp;

		input dorst;

		begin
			integer i, rcv;

			rxd = 2'b00;
			crsdv = 1'b0;
			rcv = 0;
			ok = 1;

			if (dorst) begin
				rst = 1'b1;
				#`CP;
			end

			rst = 1'b0;
			#`CP;

			`CHECK(axiov === 0, ok, "axiov != 0 @ start");

			for (i = 0; i < `CRSDV_HOLD; i = i + 1) begin
				crsdv = 1'b1;
				rxd = `PREAM_FIRST;
				#`CP;

				`CHECK(axiov === 0, ok, "crs: axiov != 0");
			end

			for (i = 0; i < 64; i = i + 2) begin
				crsdv = 1'b1;
				rxd = {preamble[i], preamble[i+1]};
				#`CP;

				`CHECK(axiov === 0, ok, "preamble: bad axiov");
			end

			for (i = 0; i < `MAC_BITS; i = i + 2) begin
				crsdv = 1'b1;
				rxd = {dst[i], dst[i+1]};
				`CHECK(axiov === 0, ok, "axiov>0 in dst");

				#`CP;
			end

			for (i = 0; i < `MAC_BITS; i = i + 2) begin
				crsdv = 1'b1;
				rxd = {src[i], src[i+1]};
				`CHECK(axiov === 0, ok, "axiov>0 in src");

				#`CP;
			end

			for (i = 0; i < `ETYPE_BITS; i = i + 2) begin
				crsdv = 1'b1;
				rxd = {etype[i], etype[i+1]};
				`CHECK(axiov === 0, ok, "axiov>0 before data");

				#`CP;
			end

			for (i = 0; i < msgsize; i = i + 2) begin
				crsdv = 1'b1;
				rxd = {msg[i], msg[i+1]};

				if (axiov) begin
					`CHECK(showexp, ok, "unexpected out");
					`CHECK(rcv == 0,
					       ok,
					       "aggregate valid for >1 cycle");
					`CHECK(axiod === exp,
					       ok,
					       "axiod != expected output");
					rcv = 1;
				end

				#`CP;
			end

			rxd = 2'b00;
			crsdv = 1'b0;

			while (i < `TIMEOUT) begin
				if (axiov) begin
					`CHECK(showexp, ok, "unexpected out");
					`CHECK(rcv == 0,
					       ok,
					       "aggregate valid for >1 cycle");
					`CHECK(axiod === exp,
					       ok,
					       "axiod != expected output");
					rcv = 1;
				end

				#`CP;
				i = i + 2;
			end

			if (showexp) `CHECK(rcv, ok, "timeout");
		end
	endtask


	initial begin: CLK
		clk = 1;
		forever #`HCP clk = ~clk;
	end

	initial begin: MAIN
`ifdef MKWAVEFORM
		$dumpfile("obj/integration.vcd");
		$dumpvars(0, integrationsim);
`endif /* MKWAVEFORM */

		rxd = 2'b00;
		crsdv = 1'b0;
		rst = 1'b0;

		#`CP;

		$display("=== test 1: tiny 1-bit message ===");
		test(`TTINY, 1, 0, 0, 1);
		if (ok) $display("OK");
		else $finish();

		$display("=== test 2: 32-bit message (no FCS) ===");
		test(`T32, 32, 0, 0, 0);
		if (ok) $display("OK");
		else $finish();

		$display("=== test 3: 32-bit message (with FCS) ===");
		test(`T64, 64, `T64_EXPECT, 1, 0);
		if (ok) $display("OK");
		else $finish();

		$display("=== test 4: 96-bit message (with FCS) ===");
		test(`T128, 128, `T128_EXPECT, 1, 0);
		if (ok) $display("OK");
		else $finish();

		$display("=== test 5: one more 32 bit message (+ FCS) ===");
		test(`T64, 64, `T64_EXPECT, 1, 0);
		if (ok) $display("OK");
		else $finish();

		$display("=== all tests passed ===");
		$finish();
	end
endmodule
