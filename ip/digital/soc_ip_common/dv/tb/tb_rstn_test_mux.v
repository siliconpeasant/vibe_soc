`timescale 1ns / 1ps

module tb_rstn_test_mux;

    // -------------------------------------------------------------------------
    // DUT signals
    // -------------------------------------------------------------------------
    reg  rst_n;
    reg  test_rst_n;
    reg  test_mode;
    wire rst_n_out;

    // -------------------------------------------------------------------------
    // DUT instantiation (crg-gen port names)
    // -------------------------------------------------------------------------
    rstn_test_mux u_dut (
        .test_md   (test_mode),
        .rstn_in   (rst_n),
        .test_rstn (test_rst_n),
        .rstn_out  (rst_n_out)
    );

    // -------------------------------------------------------------------------
    // Test statistics
    // -------------------------------------------------------------------------
    integer errors;
    integer passes;
    integer total;

    // -------------------------------------------------------------------------
    // Task: check one vector
    // -------------------------------------------------------------------------
    task check;
        input        exp_rst_n_out;
        input [63:0] tc_name;  // string
        begin
            #1;
            total = total + 1;
            if (rst_n_out !== exp_rst_n_out) begin
                $display("[FAIL] %0s | rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b (expect %b)",
                         tc_name, rst_n, test_rst_n, test_mode, rst_n_out, exp_rst_n_out);
                errors = errors + 1;
            end else begin
                $display("[PASS] %0s | rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b",
                         tc_name, rst_n, test_rst_n, test_mode, rst_n_out);
                passes = passes + 1;
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Main test sequence
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_rstn_test_mux);

        $display("============================================================");
        $display("  rstn_test_mux Testbench");
        $display("============================================================");

        errors = 0;
        passes = 0;
        total  = 0;

        // -----------------------------------------------------------------
        // TC-001: Functional mode (test_mode=0), all rst_n combinations
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-001: Functional mode (test_mode=0) ---");
        test_mode = 1'b0;

        rst_n = 1'b0; test_rst_n = 1'b0;
        check(1'b0, "TC-001.1");

        rst_n = 1'b0; test_rst_n = 1'b1;
        check(1'b0, "TC-001.2");

        rst_n = 1'b1; test_rst_n = 1'b0;
        check(1'b1, "TC-001.3");

        rst_n = 1'b1; test_rst_n = 1'b1;
        check(1'b1, "TC-001.4");

        // -----------------------------------------------------------------
        // TC-002: Test mode (test_mode=1), all test_rst_n combinations
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-002: Test mode (test_mode=1) ---");
        test_mode = 1'b1;

        rst_n = 1'b0; test_rst_n = 1'b0;
        check(1'b0, "TC-002.1");

        rst_n = 1'b0; test_rst_n = 1'b1;
        check(1'b1, "TC-002.2");

        rst_n = 1'b1; test_rst_n = 1'b0;
        check(1'b0, "TC-002.3");

        rst_n = 1'b1; test_rst_n = 1'b1;
        check(1'b1, "TC-002.4");

        // -----------------------------------------------------------------
        // TC-003: Toggle test_mode while inputs differ (0->1)
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-003: Toggle test_mode 0->1 while inputs differ ---");
        rst_n = 1'b1; test_rst_n = 1'b0; test_mode = 1'b0;
        #1;
        if (rst_n_out !== 1'b1) begin
            $display("[FAIL] TC-003 pre-check | rst_n_out=%b (expect 1)", rst_n_out);
            errors = errors + 1;
        end else begin
            $display("[PASS] TC-003 pre-check | rst_n_out=1 (test_mode=0)");
            passes = passes + 1;
        end
        total = total + 1;

        test_mode = 1'b1;
        #1;
        if (rst_n_out !== 1'b0) begin
            $display("[FAIL] TC-003 post-check | rst_n_out=%b (expect 0)", rst_n_out);
            errors = errors + 1;
        end else begin
            $display("[PASS] TC-003 post-check | rst_n_out=0 (test_mode=1)");
            passes = passes + 1;
        end
        total = total + 1;

        // -----------------------------------------------------------------
        // TC-004: Toggle test_mode while inputs differ (1->0)
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-004: Toggle test_mode 1->0 while inputs differ ---");
        rst_n = 1'b0; test_rst_n = 1'b1; test_mode = 1'b1;
        #1;
        if (rst_n_out !== 1'b1) begin
            $display("[FAIL] TC-004 pre-check | rst_n_out=%b (expect 1)", rst_n_out);
            errors = errors + 1;
        end else begin
            $display("[PASS] TC-004 pre-check | rst_n_out=1 (test_mode=1)");
            passes = passes + 1;
        end
        total = total + 1;

        test_mode = 1'b0;
        #1;
        if (rst_n_out !== 1'b0) begin
            $display("[FAIL] TC-004 post-check | rst_n_out=%b (expect 0)", rst_n_out);
            errors = errors + 1;
        end else begin
            $display("[PASS] TC-004 post-check | rst_n_out=0 (test_mode=0)");
            passes = passes + 1;
        end
        total = total + 1;

        // -----------------------------------------------------------------
        // TC-005: Both resets asserted simultaneously
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-005: Both resets asserted simultaneously ---");
        rst_n = 1'b0; test_rst_n = 1'b0; test_mode = 1'b0;
        check(1'b0, "TC-005.1 (func mode)");

        rst_n = 1'b0; test_rst_n = 1'b0; test_mode = 1'b1;
        check(1'b0, "TC-005.2 (test mode)");

        // -----------------------------------------------------------------
        // TC-006: Both resets released simultaneously
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-006: Both resets released simultaneously ---");
        rst_n = 1'b1; test_rst_n = 1'b1; test_mode = 1'b0;
        check(1'b1, "TC-006.1 (func mode)");

        rst_n = 1'b1; test_rst_n = 1'b1; test_mode = 1'b1;
        check(1'b1, "TC-006.2 (test mode)");

        // -----------------------------------------------------------------
        // TC-007: Full truth table (8 combinations)
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-007: Full truth table exhaustive ---");
        begin : truth_table
            integer i;
            reg expected;
            for (i = 0; i < 8; i = i + 1) begin
                {rst_n, test_rst_n, test_mode} = i[2:0];
                expected = test_mode ? test_rst_n : rst_n;
                #1;
                total = total + 1;
                if (rst_n_out !== expected) begin
                    $display("[FAIL] TT[%0d] rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b (expect %b)",
                             i, rst_n, test_rst_n, test_mode, rst_n_out, expected);
                    errors = errors + 1;
                end else begin
                    $display("[PASS] TT[%0d] rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b",
                             i, rst_n, test_rst_n, test_mode, rst_n_out);
                    passes = passes + 1;
                end
            end
        end

        // -----------------------------------------------------------------
        // TC-008: Random vectors
        // -----------------------------------------------------------------
        $display("");
        $display("--- TC-008: Random vectors (16 groups) ---");
        begin : random_test
            integer j;
            reg expected;
            for (j = 0; j < 16; j = j + 1) begin
                rst_n      = $random;
                test_rst_n = $random;
                test_mode  = $random;
                expected   = test_mode ? test_rst_n : rst_n;
                #1;
                total = total + 1;
                if (rst_n_out !== expected) begin
                    $display("[FAIL] RAND[%0d] rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b (expect %b)",
                             j, rst_n, test_rst_n, test_mode, rst_n_out, expected);
                    errors = errors + 1;
                end else begin
                    $display("[PASS] RAND[%0d] rst_n=%b test_rst_n=%b test_mode=%b | rst_n_out=%b",
                             j, rst_n, test_rst_n, test_mode, rst_n_out);
                    passes = passes + 1;
                end
            end
        end

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        $display("");
        $display("============================================================");
        $display("  Test summary: PASS=%0d ERROR=%0d (total=%0d)", passes, errors, total);
        if (errors == 0) begin
            $display("  RESULT: ALL TESTS PASS");
        end else begin
            $display("  RESULT: %0d TEST(S) FAILED", errors);
        end
        $display("============================================================");

        $finish;
    end

    // Timeout guard
    initial begin
        #2000;
        $display("TIMEOUT: Simulation exceeded 2000 ns");
        $finish;
    end

endmodule
