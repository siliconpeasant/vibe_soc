`timescale 1ns / 1ps

module tb_std_cell_mux;

    parameter WIDTH = 8;

    reg              sel;
    reg  [WIDTH-1:0] a;
    reg  [WIDTH-1:0] b;
    wire [WIDTH-1:0] y;

    std_cell_mux #(
        .WIDTH(WIDTH)
    ) u_dut (
        .sel (sel),
        .a   (a),
        .b   (b),
        .y   (y)
    );

    // 1-bit DUT for exhaustive test
    reg  sel1, a1, b1;
    wire y1;
    std_cell_mux #(
        .WIDTH(1)
    ) u_dut_1bit (
        .sel (sel1),
        .a   (a1),
        .b   (b1),
        .y   (y1)
    );

    integer i;
    integer errors;

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_mux);

        $display("========================================");
        $display("  std_cell_mux Testbench (WIDTH=%0d)", WIDTH);
        $display("========================================");

        errors = 0;

        // Test 1: sel=0 => y=a
        sel = 1'b0;
        a   = 8'hA5;
        b   = 8'h5A;
        #1;
        if (y !== a) begin
            $display("[FAIL] sel=0, a=%h, b=%h, y=%h (expect %h)", a, b, y, a);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=0, y=a (%h)", y);
        end

        // Test 2: sel=1 => y=b
        sel = 1'b1;
        #1;
        if (y !== b) begin
            $display("[FAIL] sel=1, a=%h, b=%h, y=%h (expect %h)", a, b, y, b);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=1, y=b (%h)", y);
        end

        // Test 3: 边界值 - 全 0 / 全 1
        sel = 1'b0;
        a   = {WIDTH{1'b0}};
        b   = {WIDTH{1'b1}};
        #1;
        if (y !== a) begin
            $display("[FAIL] sel=0, a=%h, y=%h (expect %h)", a, y, a);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=0, all-zero a");
        end

        sel = 1'b1;
        #1;
        if (y !== b) begin
            $display("[FAIL] sel=1, b=%h, y=%h (expect %h)", b, y, b);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=1, all-one b");
        end

        // Test 4: sel 切换测试
        for (i = 0; i < 16; i = i + 1) begin
            sel = $random;
            a   = $random;
            b   = $random;
            #1;
            if (y !== (sel ? b : a)) begin
                $display("[FAIL] sel=%b, a=%h, b=%h, y=%h (expect %h)",
                         sel, a, b, y, sel ? b : a);
                errors = errors + 1;
            end
        end
        $display("[PASS] 16 random sel toggle tests");

        // Test 5: 1-bit 宽度穷举测试
        for (i = 0; i < 8; i = i + 1) begin
            {sel1, a1, b1} = i[2:0];
            #1;
            if (y1 !== (sel1 ? b1 : a1)) begin
                $display("[FAIL] WIDTH=1 sel=%b a=%b b=%b y=%b (expect %b)",
                         sel1, a1, b1, y1, sel1 ? b1 : a1);
                errors = errors + 1;
            end
        end
        $display("[PASS] WIDTH=1 exhaustive test");

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
