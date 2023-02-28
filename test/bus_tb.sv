`default_nettype none
`timescale 1ns/1ps

module bus_tb;
// https://www.youtube.com/watch?v=WCOAr-96bGc

//boilerplate
logic clk;
logic rst;

// uart inputs and outputs 
logic rxd;
logic [7:0] uart_rx_axiod;
logic uart_rx_axiov;

logic txd;
logic [7:0] uart_tx_axiid;
logic uart_tx_axiiv;
logic uart_tx_axiir;

// the parameter will all get filled out in manta's big instantiator thing hehehee
parameter ADDR_WIDTH = 0; // $clog2( how much memory we need rounded up to the nearest 8 )
parameter DATA_WIDTH = 0;

// request bus, gets connected to uart_rx (through a FSM)
logic [ADDR_WIDTH-1:0] req_addr;
logic [DATA_WIDTH-1:0] req_data;
logic req_rw;
logic req_valid;
logic req_ready; 

// response bus, get connected to uart_tx (through a FSM, but the data's there in spirit)
logic res_valid;
logic res_ready;
logic res_data;

uart_rx #(
    .DATA_WDITH(8),
    .CLK_FREQ_HZ(100_000_000),
    .BAUDRATE(115200))
    uart_rx_uut (
    .clk(clk),
    .rst(rst),
    .rxd(rxd),

    .axiod(uart_rx_axiod),
    .axiov(uart_rx_axiov));

uart_tx #(
    .DATA_WDITH(8),
    .CLK_FREQ_HZ(100_000_000),
    .BAUDRATE(115200))
    uart_tx_uut (
    .clk(clk),
    .rst(rst),
    .txd(txd),

    .axiid(uart_tx_axiid),
    .axiiv(uart_tx_axiiv),
    .axiir(uart_tx_axiir));

bridge_rx bridge_rx_uut(
    .clk(clk),
    .rst(rst),

    // connect to uart_rx
    .axiid(uart_rx_axiod),
    .axiiv(uart_rx_axiov),
    
    .req_addr(req_addr),
    .req_data(req_data),
    .req_rw(req_rw),
    .req_valid(req_valid),
    .req_ready(req_ready));

bridge_tx bridge_tx_uut(
    .clk(clk),
    .rst(rst),

    // connect to uart_tx
    .axiod(uart_tx_axiid),
    .axiov(uart_tx_axiiv),
    .axior(uart_tx_axiir),
    
    .res_valid(res_valid),
    .res_ready(res_ready),
    .res_data(res_data));

always begin
    #5;
    clk = !clk;
end

initial begin
    $dumpfile("bus.vcd");
    $dumpvars(0, bus_tb);


end


endmodule



`default_nettype wire