`default_nettype none
`timescale 1ns / 1ps

module manta_tb();
    logic clk;
    logic rst;
    logic rxd;
    logic txd;


    logic probe0, probe1, probe2;
    assign probe0 = count[0];
    assign probe1 = count[1];
    assign probe2 = count[2];

    // manta
    // later make this a `MANTA that gets loaded from a svh file that the python script generates
    manta #(.FIFO_DEPTH(64)) manta(
        .clk(clk),
        .rst(rst),
        .probe0(probe0),
        .probe1(probe1),
        .probe2(probe2),
        
        .rxd(rxd),
        .txd(txd));

    /* Signal Generator */
    logic [7:0] count = 0;
    always begin 
        count = count + 1;
        #10;
    end

  	always begin
    		#5;
    		clk = !clk;
  	end

    logic [9:0] uart_data;

  	initial begin
    	$dumpfile("manta.vcd");
    	$dumpvars(0, manta_tb);
		clk = 0;
		rst = 1;
        rxd = 1;
        uart_data = 0;
        #10;
        rst = 0;

        // Wait a little bit to make sure that it doesn't like, explode or something
        #1000;
		
		// send arm byte!
        uart_data = {1'b1, 8'b00110000, 1'b0};
        for (int i=0; i < 10; i++) begin
            rxd = uart_data[i];
            #8680;
        end
        
        // see what happens lmao
		#15000000;

		$finish();
	end
endmodule

`default_nettype wire
