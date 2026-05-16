`timescale 1ns / 1ps

module tb_std_cell_inv;

    parameter WIDTH = 8;

    reg  [WIDTH-1:0] a;
    wire [WIDTH-1:0] y;

    std_cell_inv #(
        .WIDTH(WIDTH)
    ) u_dut (
        .a (a),
        .y (y)
    );

    // 1-bit DUT for exhaustive test
    reg  a1;
    wire y1;
    std_cell_inv #(
        .WIDTH(1)
    ) u_dut_1bit (
        .a (a1),
        .y (y1)
    );

    integer i;
    integer errors;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_inv);

        $display("========================================");
        $display("  std_cell_inv Testbench (WIDTH=%0d)", WIDTH);
        $display("========================================");

        errors = 0;

        // Test 1: basic inversion
        a = 8'hA5; #1;
        if (y !== (~a)) begin
            $display("[FAIL] a=%h, y=%h (expect %h)", a, y, ~a);
            errors = errors + 1;
        end else begin
            $display("[PASS] a=%h => y=%h", a, y);
        end

        // Test 2: all-zero input => all-one output
        a = {WIDTH{1'b0}}; #1;
        if (y !== {WIDTH{1'b1}}) begin
            $display("[FAIL] a=0, y=%h (expect all1)", y);
            errors = errors + 1;
        end else begin
            $display("[PASS] all-zero a => y=all1");
        end

        // Test 3: all-one input => all-zero output
        a = {WIDTH{1'b1}}; #1;
        if (y !== {WIDTH{1'b0}}) begin
            $display("[FAIL] a=all1, y=%h (expect 0)", y);
            errors = errors + 1;
        end else begin
            $display("[PASS] all-one a => y=0");
        end

        // Test 4: random vectors
        for (i = 0; i < 32; i = i + 1) begin
            a = $random;
            #1;
            if (y !== (~a)) begin
                $display("[FAIL] a=%h, y=%h (expect %h)", a, y, ~a);
                errors = errors + 1;
            end
        end
        $display("[PASS] 32 random vectors");

        // Test 5: 1-bit exhaustive truth table
        for (i = 0; i < 2; i = i + 1) begin
            a1 = i[0];
            #1;
            if (y1 !== (~a1)) begin
                $display("[FAIL] WIDTH=1 a=%b y=%b (expect %b)",
                         a1, y1, ~a1);
                errors = errors + 1;
            end
        end
        $display("[PASS] WIDTH=1 exhaustive truth table");

        $display("========================================");
        if (errors == 0) begin
            $display("  All tests PASSED!");
        end else begin
            $display("  %0d test(s) FAILED!", errors);
        end
        $display("========================================");
        $finish;
    end

endmodule
