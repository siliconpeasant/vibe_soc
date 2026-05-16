`timescale 1ns / 1ps

// -----------------------------------------------------------------------------
// Testbench : tb_std_cell_buf
// Function  : Functional verification for std_cell_buf (y = a, parameterized WIDTH)
// Strategy  :
//   1. WIDTH=8 classic patterns (00, FF, A5, 5A, 01, 80, 0F, F0)
//   2. WIDTH=1 exhaustive truth table (a = 0/1)
//   3. WIDTH=8 random vectors (256 cases)
// Pass cond : total_checks > 0 && errors == 0  ->  prints "[TB] PASS"
// -----------------------------------------------------------------------------

module tb_std_cell_buf;

    parameter WIDTH = 8;

    // WIDTH=8 main DUT
    reg  [WIDTH-1:0] a;
    wire [WIDTH-1:0] y;

    std_cell_buf #(
        .WIDTH(WIDTH)
    ) u_dut (
        .a (a),
        .y (y)
    );

    // WIDTH=1 exhaustive DUT
    reg  a1;
    wire y1;
    std_cell_buf #(
        .WIDTH(1)
    ) u_dut_1bit (
        .a (a1),
        .y (y1)
    );

    integer i;
    integer errors;
    integer total_checks;

    // -------------------------------------------------------------------------
    // Task: check_w8
    // -------------------------------------------------------------------------
    task check_w8;
        input [WIDTH-1:0] stim;
        begin
            a = stim; #1;
            total_checks = total_checks + 1;
            if (y !== stim) begin
                $display("ERROR: [W8] a=%h, y=%h (expect %h)", a, y, stim);
                errors = errors + 1;
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Task: check_w1
    // -------------------------------------------------------------------------
    task check_w1;
        input stim;
        begin
            a1 = stim; #1;
            total_checks = total_checks + 1;
            if (y1 !== stim) begin
                $display("ERROR: [W1] a=%b, y=%b (expect %b)", a1, y1, stim);
                errors = errors + 1;
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Main stimulus
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_buf);

        $display("========================================");
        $display("  std_cell_buf Testbench (WIDTH=%0d)", WIDTH);
        $display("========================================");

        errors       = 0;
        total_checks = 0;
        a            = {WIDTH{1'b0}};
        a1           = 1'b0;
        #1;

        // ---------------------------------------------------------------------
        // Group 1: WIDTH=8 classic patterns
        // ---------------------------------------------------------------------
        check_w8(8'h00);
        check_w8(8'hFF);
        check_w8(8'hA5);
        check_w8(8'h5A);
        check_w8(8'h01);
        check_w8(8'h80);
        check_w8(8'h0F);
        check_w8(8'hF0);

        // ---------------------------------------------------------------------
        // Group 2: WIDTH=1 exhaustive truth table
        // ---------------------------------------------------------------------
        check_w1(1'b0);
        check_w1(1'b1);

        // ---------------------------------------------------------------------
        // Group 3: WIDTH=8 random 256 vectors
        // ---------------------------------------------------------------------
        for (i = 0; i < 256; i = i + 1) begin
            check_w8($random & 8'hFF);
        end

        // ---------------------------------------------------------------------
        // Summary
        // ---------------------------------------------------------------------
        $display("========================================");
        $display("Result: %0d PASS, %0d ERROR", total_checks, errors);
        if (errors == 0) $display("[TB] PASS");
        else             $display("[TB] FAIL");
        $display("========================================");
        $finish;
    end

    // -------------------------------------------------------------------------
    // Watchdog
    // -------------------------------------------------------------------------
    initial begin
        #5000;
        $display("ERROR: TIMEOUT");
        $finish;
    end

endmodule
