`timescale 1ns / 1ps

module tb_std_cell_clk_mux;

    reg  clk0;
    reg  clk1;
    reg  sel;
    wire clk_out;

    std_cell_clk_mux u_dut (
        .clk0    (clk0),
        .clk1    (clk1),
        .sel     (sel),
        .clk_out (clk_out)
    );

    integer errors;

    // clk0: 10ns period
    initial begin
        clk0 = 0;
        forever #5 clk0 = ~clk0;
    end

    // clk1: 6ns period (different freq)
    initial begin
        clk1 = 0;
        forever #3 clk1 = ~clk1;
    end

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_clk_mux);

        $display("========================================");
        $display("  std_cell_clk_mux Testbench");
        $display("========================================");

        errors = 0;

        // Test 1: sel=0 => clk_out = clk0
        sel = 1'b0;
        @(posedge clk0);
        #1;
        if (clk_out !== clk0) begin
            $display("[FAIL] sel=0: clk_out=%b, expected clk0=%b", clk_out, clk0);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=0: clk_out follows clk0");
        end

        // Test 2: sel=1 => clk_out = clk1
        sel = 1'b1;
        @(posedge clk1);
        #1;
        if (clk_out !== clk1) begin
            $display("[FAIL] sel=1: clk_out=%b, expected clk1=%b", clk_out, clk1);
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=1: clk_out follows clk1");
        end

        // Test 3: toggle sel multiple times, check at each edge
        repeat (4) begin
            sel = ~sel;
            @(posedge clk0 or posedge clk1);
            #1;
            if (sel && clk_out !== clk1) begin
                $display("[FAIL] sel=1 but clk_out != clk1");
                errors = errors + 1;
            end else if (!sel && clk_out !== clk0) begin
                $display("[FAIL] sel=0 but clk_out != clk0");
                errors = errors + 1;
            end
        end
        $display("[PASS] sel toggle cross-check");

        // Test 4: sel=0 stable check
        sel = 1'b0;
        repeat (3) @(posedge clk0);
        #1;
        if (clk_out !== clk0) begin
            $display("[FAIL] sel=0 stable: clk_out mismatch");
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=0 stable check");
        end

        // Test 5: sel=1 stable check
        sel = 1'b1;
        repeat (5) @(posedge clk1);
        #1;
        if (clk_out !== clk1) begin
            $display("[FAIL] sel=1 stable: clk_out mismatch");
            errors = errors + 1;
        end else begin
            $display("[PASS] sel=1 stable check");
        end

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
