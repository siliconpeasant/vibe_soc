// lint_lab - IP Level Testbench
// Self-checking testbench, compatible with iverilog / vcs / verilator 5.0+

`timescale 1ns / 1ps

module tb_lint_lab;

    logic clk;
    logic rst_n;
    logic [7:0] data_in;
    logic       valid_in;
    logic [7:0] data_out;
    logic       valid_out;

    int         error_cnt = 0;
    int         check_cnt = 0;

    // Clock generation: 100 MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset generation
    initial begin
        rst_n = 0;
        #50;  // 5 clock cycles
        rst_n = 1;
    end

    // DUT instantiation
    lint_lab u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .data_in   (data_in),
        .valid_in  (valid_in),
        .data_out  (data_out),
        .valid_out (valid_out)
    );

    // Waveform dump
    initial begin
        $dumpfile("dv/sim/wave.vcd");
        $dumpvars(0, tb_lint_lab);
    end

    // Self-checking: verify output when valid_out is high
    always @(posedge clk) begin
        if (valid_out) begin
            check_cnt++;
            if (data_out !== (data_in + 1'b1)) begin
                $error("[FAIL] check #%0d: expected 0x%02X, got 0x%02X",
                       check_cnt, data_in + 1'b1, data_out);
                error_cnt++;
            end else begin
                $display("[PASS] check #%0d: data_out = 0x%02X (expected 0x%02X)",
                         check_cnt, data_out, data_in + 1'b1);
            end
        end
    end

    // Stimulus
    initial begin
        $display("==================================");
        $display(" lint_lab IP Simulation Start ");
        $display("==================================");

        data_in  = 8'h00;
        valid_in = 1'b0;

        #70;  // wait for reset release + 2 cycles

        // Test case 1
        #10;
        data_in  = 8'hAA;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // 5 clock cycles

        // Test case 2
        #10;
        data_in  = 8'h55;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // 5 clock cycles

        // Test case 3: boundary value 0xFF
        #10;
        data_in  = 8'hFF;
        valid_in = 1'b1;
        #10;
        valid_in = 1'b0;

        #50;  // wait for last check

        $display("==================================");
        if (error_cnt == 0)
            $display("  ALL PASSED (%0d checks)", check_cnt);
        else
            $display("  FAILED: %0d / %0d checks failed", error_cnt, check_cnt);
        $display(" lint_lab IP Simulation Done  ");
        $display("==================================");
        $finish;
    end

endmodule
