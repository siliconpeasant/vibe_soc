// io_ss - Module Level Testbench
// Placeholder: please instantiate your DUT and add stimulus

`timescale 1ns / 1ps

module tb_io_ss;

    logic clk;
    logic rst_n;

    // Clock generation: 100 MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #50;
        rst_n = 1;
    end

    // Waveform dump
    initial begin
        $dumpfile("dv/sim/wave.vcd");
        $dumpvars(0, tb_io_ss);
    end

    // TODO: Instantiate DUT here

    initial begin
        $display("==================================");
        $display(" io_ss Simulation Start ");
        $display("==================================");
        #200;
        $display("==================================");
        $display(" io_ss Simulation Done  ");
        $display("==================================");
        $finish;
    end

endmodule
