// lib - Module Level Testbench
// Placeholder: please instantiate your DUT and add stimulus

`timescale 1ns / 1ps

module tb_lib;

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
        $dumpvars(0, tb_lib);
    end

    // TODO: Instantiate DUT here

    initial begin
        $display("==================================");
        $display(" lib Simulation Start ");
        $display("==================================");
        #200;
        $display("==================================");
        $display(" lib Simulation Done  ");
        $display("==================================");
        $finish;
    end

endmodule
