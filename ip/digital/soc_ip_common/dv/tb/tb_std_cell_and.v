`timescale 1ns / 1ps

module tb_std_cell_and;

    parameter WIDTH = 8;

    reg  [WIDTH-1:0] a;
    reg  [WIDTH-1:0] b;
    wire [WIDTH-1:0] y;

    std_cell_and #(
        .WIDTH(WIDTH)
    ) u_dut (
        .a (a),
        .b (b),
        .y (y)
    );

    // 1-bit DUT for exhaustive test
    reg  a1, b1;
    wire y1;
    std_cell_and #(
        .WIDTH(1)
    ) u_dut_1bit (
        .a (a1),
        .b (b1),
        .y (y1)
    );

    integer i;
    integer errors;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_and);

        $display("========================================");
        $display("  std_cell_and Testbench (WIDTH=%0d)", WIDTH);
        $display("========================================");

        errors = 0;

        // Test 1: 基本与门真值表
        a = 8'hA5; b = 8'h5A; #1;
        if (y !== (a & b)) begin
            $display("[FAIL] a=%h, b=%h, y=%h (expect %h)", a, b, y, a & b);
            errors = errors + 1;
        end else begin
            $display("[PASS] a=%h & b=%h = %h", a, b, y);
        end

        // Test 2: 全 0 / 全 1 边界
        a = {WIDTH{1'b0}}; b = {WIDTH{1'b1}}; #1;
        if (y !== {WIDTH{1'b0}}) begin
            $display("[FAIL] a=0, b=all1, y=%h (expect 0)", y);
            errors = errors + 1;
        end else begin
            $display("[PASS] all-zero a => y=0");
        end

        a = {WIDTH{1'b1}}; b = {WIDTH{1'b1}}; #1;
        if (y !== {WIDTH{1'b1}}) begin
            $display("[FAIL] a=all1, b=all1, y=%h (expect all1)", y);
            errors = errors + 1;
        end else begin
            $display("[PASS] all-one inputs => y=all1");
        end

        a = {WIDTH{1'b1}}; b = {WIDTH{1'b0}}; #1;
        if (y !== {WIDTH{1'b0}}) begin
            $display("[FAIL] a=all1, b=0, y=%h (expect 0)", y);
            errors = errors + 1;
        end else begin
            $display("[PASS] all-one a, zero b => y=0");
        end

        // Test 3: 随机测试
        for (i = 0; i < 32; i = i + 1) begin
            a = $random;
            b = $random;
            #1;
            if (y !== (a & b)) begin
                $display("[FAIL] a=%h, b=%h, y=%h (expect %h)", a, b, y, a & b);
                errors = errors + 1;
            end
        end
        $display("[PASS] 32 random vectors");

        // Test 4: 1-bit 穷举（与门真值表）
        for (i = 0; i < 4; i = i + 1) begin
            {a1, b1} = i[1:0];
            #1;
            if (y1 !== (a1 & b1)) begin
                $display("[FAIL] WIDTH=1 a=%b b=%b y=%b (expect %b)",
                         a1, b1, y1, a1 & b1);
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
