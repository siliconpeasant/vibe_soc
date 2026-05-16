`timescale 1ns / 1ps

module tb_std_cell_icg;

    reg  clk;
    reg  en;
    reg  test_en;
    wire gated_clk;

    std_cell_icg u_dut (
        .clk       (clk),
        .en        (en),
        .test_en   (test_en),
        .gated_clk (gated_clk)
    );

    integer errors;
    integer passes;
    integer i;

    // Clock generation: 10ns period
    initial begin
        clk = 1'b0;
    end
    always #5 clk = ~clk;

    // Timeout guard
    initial begin
        #2000;
        $display("TIMEOUT after 2000ns");
        $finish;
    end

    // Task: check gated_clk value at current time
    task check_gated;
        input expected;
        input [255:0] msg;
        begin
            if (gated_clk !== expected) begin
                $display("[FAIL] @%0tns %s | gated_clk=%b (expect %b)",
                         $time, msg, gated_clk, expected);
                errors = errors + 1;
            end else begin
                $display("[PASS] @%0tns %s | gated_clk=%b",
                         $time, msg, gated_clk);
                passes = passes + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_icg);

        $display("========================================");
        $display("  std_cell_icg Testbench");
        $display("========================================");

        errors = 0;
        passes = 0;

        // ------------------------------------------------
        // Test 1: Basic gating - en=0, gated_clk stays low
        // ------------------------------------------------
        $display("\n--- Test 1: Basic gating (en=0) ---");
        en = 1'b0;
        test_en = 1'b0;
        // Wait for clk to go low, latch captures en|test_en = 0
        @(negedge clk);
        #1;
        // Now clk is low, en_latch should be 0
        // Check during next high phase: gated_clk should be 0
        @(posedge clk);
        #1;
        check_gated(1'b0, "en=0, clk high => gated_clk=0");

        @(negedge clk);
        #1;
        check_gated(1'b0, "en=0, clk low => gated_clk=0");

        // Run a few more cycles to confirm stability
        repeat(3) begin
            @(posedge clk);
            #1;
            check_gated(1'b0, "en=0 stable, clk high => gated_clk=0");
        end

        // ------------------------------------------------
        // Test 2: Enable pass-through - en=1, gated_clk follows clk
        // ------------------------------------------------
        $display("\n--- Test 2: Enable pass-through (en=1) ---");
        // Set en=1 during clk low so latch captures it
        @(negedge clk);
        en = 1'b1;
        #1;
        // Now en_latch should be 1
        @(posedge clk);
        #1;
        check_gated(1'b1, "en=1, clk high => gated_clk=1");

        @(negedge clk);
        #1;
        check_gated(1'b0, "en=1, clk low => gated_clk=0");

        @(posedge clk);
        #1;
        check_gated(1'b1, "en=1, clk high => gated_clk=1");

        // ------------------------------------------------
        // Test 3: test_en DFT override - test_en=1 forces clk through
        // ------------------------------------------------
        $display("\n--- Test 3: test_en DFT override ---");
        // First disable en, then assert test_en
        @(negedge clk);
        en = 1'b0;
        test_en = 1'b1;
        #1;
        // en_latch should capture en|test_en = 1
        @(posedge clk);
        #1;
        check_gated(1'b1, "en=0, test_en=1, clk high => gated_clk=1 (DFT)");

        @(negedge clk);
        #1;
        check_gated(1'b0, "en=0, test_en=1, clk low => gated_clk=0");

        // Now try en=1, test_en=1 (both high)
        @(negedge clk);
        en = 1'b1;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "en=1, test_en=1, clk high => gated_clk=1");

        // Deassert test_en, keep en=1
        @(negedge clk);
        test_en = 1'b0;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "en=1, test_en=0, clk high => gated_clk=1");

        // ------------------------------------------------
        // Test 4: Glitch-free - en changes during clk HIGH
        //         should NOT affect gated_clk until next low phase
        // ------------------------------------------------
        $display("\n--- Test 4: Glitch-free (en changes during clk high) ---");
        // Start with en=1, ensure latch is high
        @(negedge clk);
        en = 1'b1;
        test_en = 1'b0;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "pre-glitch: en=1, clk high => gated_clk=1");

        // Now deassert en while clk is HIGH - latch should NOT be transparent
        // so en_latch stays 1, gated_clk should stay 1 while clk is high
        en = 1'b0;
        #2;
        check_gated(1'b1, "glitch test: en=0 during clk high, gated_clk still=1");

        // Wait for clk to go low, latch will now capture en=0
        @(negedge clk);
        #1;
        check_gated(1'b0, "after negedge: en=0 captured, clk low => gated_clk=0");

        // Next posedge: gated_clk should be 0
        @(posedge clk);
        #1;
        check_gated(1'b0, "after en captured as 0, clk high => gated_clk=0");

        // Reverse: assert en during clk HIGH - should not affect until negedge
        @(posedge clk);
        #1;
        en = 1'b1;
        #2;
        // gated_clk should still be 0 because latch captured 0 when clk was low
        check_gated(1'b0, "glitch test: en=1 during clk high, gated_clk still=0");

        // Wait for negedge to capture en=1
        @(negedge clk);
        #1;
        check_gated(1'b0, "after negedge captures en=1, clk low => gated_clk=0");

        @(posedge clk);
        #1;
        check_gated(1'b1, "after en=1 captured, clk high => gated_clk=1");

        // ------------------------------------------------
        // Test 5: Timing setup - en changes during clk LOW,
        //         next posedge responds correctly
        // ------------------------------------------------
        $display("\n--- Test 5: Timing setup (en changes during clk low) ---");
        // Ensure en=1 is latched
        @(negedge clk);
        en = 1'b1;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "setup: en=1 latched, clk high => gated_clk=1");

        // Change en to 0 during clk LOW
        @(negedge clk);
        #2; // small delay into low phase
        en = 1'b0;
        #1;
        // Latch is transparent when clk is low, so en_latch should now be 0
        @(posedge clk);
        #1;
        check_gated(1'b0, "en changed during clk low, next posedge => gated_clk=0");

        // Change en to 1 during clk LOW
        @(negedge clk);
        #2;
        en = 1'b1;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "en changed during clk low, next posedge => gated_clk=1");

        // ------------------------------------------------
        // Test 6: test_en glitch-free during clk high
        // ------------------------------------------------
        $display("\n--- Test 6: test_en glitch-free during clk high ---");
        // Start with en=0, test_en=0
        @(negedge clk);
        en = 1'b0;
        test_en = 1'b0;
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b0, "pre-glitch: en=0, test_en=0 => gated_clk=0");

        // Assert test_en during clk HIGH - should not affect immediately
        test_en = 1'b1;
        #2;
        check_gated(1'b0, "test_en=1 during clk high, gated_clk still=0");

        // Wait for negedge to capture
        @(negedge clk);
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b1, "test_en captured at negedge, next posedge => gated_clk=1");

        // Deassert test_en during clk HIGH
        test_en = 1'b0;
        #2;
        check_gated(1'b1, "test_en=0 during clk high, gated_clk still=1");

        @(negedge clk);
        #1;
        @(posedge clk);
        #1;
        check_gated(1'b0, "test_en=0 captured, next posedge => gated_clk=0");

        // ------------------------------------------------
        // Test 7: Random test - 16 random en/test_en transitions
        // ------------------------------------------------
        $display("\n--- Test 7: Random transitions ---");
        for (i = 0; i < 16; i = i + 1) begin
            @(negedge clk);
            en = $random;
            test_en = $random;
            #1;
            // Latch value when clk is low
            @(posedge clk);
            #1;
            // Expected: gated_clk = clk & (en | test_en) evaluated at latch capture time
            // Since we set en/test_en at negedge and latch is transparent when clk low,
            // en_latch = en | test_en, and gated_clk = clk & en_latch
            // At posedge, clk=1, so gated_clk should equal en_latch
            if (gated_clk !== (en | test_en)) begin
                $display("[FAIL] @%0tns random[%0d] en=%b test_en=%b gated_clk=%b (expect %b)",
                         $time, i, en, test_en, gated_clk, en | test_en);
                errors = errors + 1;
            end else begin
                $display("[PASS] @%0tns random[%0d] en=%b test_en=%b gated_clk=%b",
                         $time, i, en, test_en, gated_clk);
                passes = passes + 1;
            end
        end

        // ------------------------------------------------
        // Test 8: test_en=1, en random - DFT always forces through
        // ------------------------------------------------
        $display("\n--- Test 8: test_en=1 with random en (DFT mode) ---");
        @(negedge clk);
        test_en = 1'b1;
        for (i = 0; i < 8; i = i + 1) begin
            @(negedge clk);
            en = $random;
            #1;
            @(posedge clk);
            #1;
            // test_en=1 => en_latch always 1 => gated_clk always follows clk
            if (gated_clk !== 1'b1) begin
                $display("[FAIL] @%0tns DFT[%0d] en=%b test_en=1 gated_clk=%b (expect 1)",
                         $time, i, en, gated_clk);
                errors = errors + 1;
            end else begin
                $display("[PASS] @%0tns DFT[%0d] en=%b test_en=1 gated_clk=1",
                         $time, i, en);
                passes = passes + 1;
            end
        end

        // ------------------------------------------------
        // Test 9: en=0, test_en=0 - gated_clk always 0
        // ------------------------------------------------
        $display("\n--- Test 9: Both en and test_en low ---");
        @(negedge clk);
        en = 1'b0;
        test_en = 1'b0;
        #1;
        repeat(4) begin
            @(posedge clk);
            #1;
            check_gated(1'b0, "en=0, test_en=0 => gated_clk=0");
            @(negedge clk);
            #1;
            check_gated(1'b0, "en=0, test_en=0 => gated_clk=0");
        end

        // ------------------------------------------------
        // Summary
        // ------------------------------------------------
        $display("\n========================================");
        $display("Test summary: PASS=%0d ERROR=%0d", passes, errors);
        if (errors == 0) begin
            $display("RESULT: ALL TESTS PASS");
        end else begin
            $display("RESULT: %0d TEST(S) FAILED", errors);
        end
        $display("========================================");

        $finish;
    end

endmodule
