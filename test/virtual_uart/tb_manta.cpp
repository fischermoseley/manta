#include <stdlib.h>
#include <iostream>
#include <string>
#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vmanta.h"

vluint64_t sim_time = 0;

int main(int argc, char** argv, char** env) {
    Vmanta *dut = new Vmanta;

    Verilated::traceEverOn(true);
    VerilatedVcdC *m_trace = new VerilatedVcdC;
    dut->trace(m_trace, 5);
    m_trace->open("waveform.vcd");

    while(true) {

    // get line from stdin
    std::string line;
    std::getline(std::cin, line);

    for (int i=0; i < line.length(); i++) {
         // advance simulation
        dut->clk ^= 1;
        dut->mem_clk ^= 1;
        dut->eval();
        m_trace->dump(sim_time);
        sim_time++;

        // feed it to the serial port
        dut->urx_brx_axiv = 1;
        dut->urx_brx_axid = line[i];

        if (line[i] == 'C')
            dut->urx_brx_axid = '\r';

        if (line[i] == 'L')
            dut->urx_brx_axid = '\n';

        // advance simulation
        dut->clk ^= 1;
        dut->mem_clk ^= 1;
        dut->eval();
        m_trace->dump(sim_time);
        sim_time++;
    }

    for (int i=0; i < 30; i++) {

         // advance simulation
        dut->clk ^= 1;
        dut->mem_clk ^= 1;
        dut->eval();
        m_trace->dump(sim_time);
        sim_time++;


        // print whatever's on the port
        if(dut->btx_utx_start)
            std::cout << dut->btx_utx_data;

         // advance simulation
        dut->clk ^= 1;
        dut->mem_clk ^= 1;
        dut->eval();
        m_trace->dump(sim_time);
        sim_time++;
    }


    }

    m_trace->close();
    delete dut;
    exit(EXIT_SUCCESS);
}
