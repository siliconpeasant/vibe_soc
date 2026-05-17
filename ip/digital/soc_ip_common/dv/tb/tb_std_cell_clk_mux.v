`timescale 1ns / 1ps

module tb_std_cell_clk_mux;

    reg  clk0;
    reg  clk1;
    reg  sel;
    reg  clk_en;
    wire clk_out;

    std_cell_clk_mux u_dut (
        .clk0    (clk0),
        .clk1    (clk1),
        .sel     (sel),
        .clk_en  (clk_en),
        .clk_out (clk_out)
    );

    integer errors;
    integer passes;
    integer i;

    // Clock generation: clk0 = 10ns period (fast)
    initial begin
        clk0 = 1'b0;
    end
    always #5 clk0 = ~clk0;

    // Clock generation: clk1 = 20ns period (slow)
    initial begin
        clk1 = 1'b0;
    end
    always #10 clk1 = ~clk1;

    // Timeout guard
    initial begin
        #3000;
        $display("TIMEOUT after 3000ns");
        $finish;
    end

    // Task: check clk_out value at current time
    task check_output;
        input expected;
        input [255:0] msg;
        begin
            if (clk_out !== expected) begin
                $display("[FAIL] @%0tns %s | clk_out=%b (expect %b)",
                         $time, msg, clk_out, expected);
                errors = errors + 1;
            end else begin
                $display("[PASS] @%0tns %s | clk_out=%b",
                         $time, msg, clk_out);
                passes = passes + 1;
            end
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_std_cell_clk_mux);

        $display("========================================");
        $display("  std_cell_clk_mux Testbench");
        $display("  clk0 period = 10ns, clk1 period = 20ns");
        $display("========================================");

        errors = 0;
        passes = 0;

        // ------------------------------------------------
        // Test 1: Basic selection - sel=0, clk_en=1
        // clk_out should follow clk0
        // ------------------------------------------------
        $display("\n--- Test 1: Basic selection sel=0 (clk0) ---");
        sel = 1'b0;
        clk_en = 1'b1;
        @(negedge clk0);
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "sel=0, clk0 high => clk_out=1");

        @(negedge clk0);
        #1;
        check_output(1'b0, "sel=0, clk0 low => clk_out=0");

        repeat(3) begin
            @(posedge clk0);
            #1;
            check_output(1'b1, "sel=0 stable, clk0 high => clk_out=1");
            @(negedge clk0);
            #1;
            check_output(1'b0, "sel=0 stable, clk0 low => clk_out=0");
        end

        // ------------------------------------------------
        // Test 2: Basic selection - sel=1, clk_en=1
        // clk_out should follow clk1
        // ------------------------------------------------
        $display("\n--- Test 2: Basic selection sel=1 (clk1) ---");
        @(negedge clk1);
        sel = 1'b1;
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b1, "sel=1, clk1 high => clk_out=1");

        @(negedge clk1);
        #1;
        check_output(1'b0, "sel=1, clk1 low => clk_out=0");

        repeat(3) begin
            @(posedge clk1);
            #1;
            check_output(1'b1, "sel=1 stable, clk1 high => clk_out=1");
            @(negedge clk1);
            #1;
            check_output(1'b0, "sel=1 stable, clk1 low => clk_out=0");
        end

        // ------------------------------------------------
        // Test 3: Glitch-free switching - sel 0->1
        // ------------------------------------------------
        $display("\n--- Test 3: Glitch-free sel 0->1 ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "pre-switch: sel=0, clk0 high => clk_out=1");

        @(negedge clk0);
        sel = 1'b1;
        #1;
        check_output(1'b0, "sel switched 0->1, clk0 low => clk_out=0 (en0=0)");

        @(negedge clk1);
        #1;
        check_output(1'b0, "after clk1 negedge captures sel=1, clk1 low => clk_out=0");

        @(posedge clk1);
        #1;
        check_output(1'b1, "sel=1 latched, clk1 high => clk_out=1");

        // ------------------------------------------------
        // Test 4: Glitch-free switching - sel 1->0
        // ------------------------------------------------
        $display("\n--- Test 4: Glitch-free sel 1->0 ---");
        @(negedge clk1);
        sel = 1'b1;
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b1, "pre-switch: sel=1, clk1 high => clk_out=1");

        @(negedge clk1);
        sel = 1'b0;
        #1;
        check_output(1'b0, "sel switched 1->0, clk1 low => clk_out=0 (en1=0)");

        @(negedge clk0);
        #1;
        check_output(1'b0, "after clk0 negedge captures sel=0, clk0 low => clk_out=0");

        @(posedge clk0);
        #1;
        check_output(1'b1, "sel=0 latched, clk0 high => clk_out=1");

        // ------------------------------------------------
        // Test 5: Clock enable - clk_en=0 forces output to 0
        // ------------------------------------------------
        $display("\n--- Test 5: Clock enable disable (clk_en=0) ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "pre-disable: sel=0, clk_en=1, clk0 high => clk_out=1");

        @(negedge clk0);
        clk_en = 1'b0;
        #1;
        check_output(1'b0, "clk_en=0 captured, clk0 low => clk_out=0");

        @(posedge clk0);
        #1;
        check_output(1'b0, "clk_en=0, clk0 high => clk_out=0");

        repeat(3) begin
            @(posedge clk0);
            #1;
            check_output(1'b0, "clk_en=0 stable, clk0 high => clk_out=0");
            @(negedge clk0);
            #1;
            check_output(1'b0, "clk_en=0 stable, clk0 low => clk_out=0");
        end

        @(negedge clk1);
        sel = 1'b1;
        clk_en = 1'b0;
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b0, "sel=1, clk_en=0, clk1 high => clk_out=0");

        @(negedge clk1);
        #1;
        check_output(1'b0, "sel=1, clk_en=0, clk1 low => clk_out=0");

        // ------------------------------------------------
        // Test 6: Re-enable - clk_en=1 restores normal selection
        // ------------------------------------------------
        $display("\n--- Test 6: Re-enable (clk_en=1) ---");
        @(negedge clk1);
        clk_en = 1'b1;
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b1, "re-enable: sel=1, clk_en=1, clk1 high => clk_out=1");

        @(negedge clk1);
        #1;
        check_output(1'b0, "re-enable: sel=1, clk_en=1, clk1 low => clk_out=0");

        @(negedge clk0);
        sel = 1'b0;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "re-enable sel=0: clk0 high => clk_out=1");

        // ------------------------------------------------
        // Test 7: Multiple back-and-forth transitions
        // ------------------------------------------------
        $display("\n--- Test 7: Multiple back-and-forth transitions ---");
        for (i = 0; i < 6; i = i + 1) begin
            if (i % 2 == 0) begin
                @(negedge clk0);
                sel = 1'b0;
                #1;
                @(posedge clk0);
                #1;
                check_output(1'b1, "transition sel=0, clk0 high");
                @(negedge clk0);
                #1;
                check_output(1'b0, "transition sel=0, clk0 low");
            end else begin
                @(negedge clk1);
                sel = 1'b1;
                #1;
                @(posedge clk1);
                #1;
                check_output(1'b1, "transition sel=1, clk1 high");
                @(negedge clk1);
                #1;
                check_output(1'b0, "transition sel=1, clk1 low");
            end
        end

        // ------------------------------------------------
        // Test 8: Verify no runt pulses - rapid toggling
        // ------------------------------------------------
        $display("\n--- Test 8: Runt pulse detection ---");
        begin
            integer runt_found;
            runt_found = 0;

            @(negedge clk0);
            sel = 1'b0;
            clk_en = 1'b1;
            #1;
            repeat(2) @(posedge clk0);

            repeat(4) begin
                @(negedge clk0);
                sel = 1'b1;
                #1;
                @(negedge clk1);
                #1;
                @(posedge clk1);
                #1;
                if (clk_out !== 1'b1) begin
                    $display("[FAIL] @%0tns Rapid toggle: sel=1, expected clk_out=1, got %b", $time, clk_out);
                    errors = errors + 1;
                    runt_found = 1;
                end else begin
                    $display("[PASS] @%0tns Rapid toggle: sel=1, clk_out=1", $time);
                    passes = passes + 1;
                end

                @(negedge clk1);
                sel = 1'b0;
                #1;
                @(negedge clk0);
                #1;
                @(posedge clk0);
                #1;
                if (clk_out !== 1'b1) begin
                    $display("[FAIL] @%0tns Rapid toggle: sel=0, expected clk_out=1, got %b", $time, clk_out);
                    errors = errors + 1;
                    runt_found = 1;
                end else begin
                    $display("[PASS] @%0tns Rapid toggle: sel=0, clk_out=1", $time);
                    passes = passes + 1;
                end
            end

            if (!runt_found) begin
                $display("[PASS] No runt pulses detected during rapid sel toggling");
                passes = passes + 1;
            end
        end

        // ------------------------------------------------
        // Test 9: clk_en toggle during active clock
        // Verify glitch-free disable/enable
        // ------------------------------------------------
        $display("\n--- Test 9: clk_en toggle glitch-free ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "pre-toggle: sel=0, clk_en=1, clk0 high => clk_out=1");

        clk_en = 1'b0;
        #2;
        check_output(1'b1, "clk_en=0 during clk0 high, clk_out still=1");

        @(negedge clk0);
        #1;
        check_output(1'b0, "clk_en=0 captured at negedge, clk0 low => clk_out=0");

        @(posedge clk0);
        #1;
        check_output(1'b0, "clk_en=0 latched, clk0 high => clk_out=0");

        clk_en = 1'b1;
        #2;
        check_output(1'b0, "clk_en=1 during clk0 high, clk_out still=0");

        @(negedge clk0);
        #1;
        check_output(1'b0, "clk_en=1 captured at negedge, clk0 low => clk_out=0");

        @(posedge clk0);
        #1;
        check_output(1'b1, "clk_en=1 latched, clk0 high => clk_out=1");

        // ------------------------------------------------
        // Test 10: sel change with clk_en=0 (should stay 0)
        // ------------------------------------------------
        $display("\n--- Test 10: sel change while clk_en=0 ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b0;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b0, "sel=0, clk_en=0, clk0 high => clk_out=0");

        @(negedge clk1);
        sel = 1'b1;
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b0, "sel=1, clk_en=0, clk1 high => clk_out=0");

        @(negedge clk0);
        sel = 1'b0;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b0, "sel=0, clk_en=0, clk0 high => clk_out=0");

        @(negedge clk0);
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "sel=0, clk_en=1 (re-enabled), clk0 high => clk_out=1");

        // ------------------------------------------------
        // Test 11: Phase relationship test
        // Verify still works with existing clock relationship
        // ------------------------------------------------
        $display("\n--- Test 11: Phase relationship test ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "phase: sel=0, clk0 high => clk_out=1");

        @(negedge clk0);
        sel = 1'b1;
        #1;
        @(negedge clk1);
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b1, "phase: sel=1, clk1 high => clk_out=1");

        // ------------------------------------------------
        // Test 12: Random sel/clk_en transitions
        // ------------------------------------------------
        $display("\n--- Test 12: Random sel/clk_en transitions ---");
        for (i = 0; i < 16; i = i + 1) begin
            reg next_sel;
            reg next_clk_en;
            next_sel = $random;
            next_clk_en = $random;

            wait(clk0 == 1'b0 && clk1 == 1'b0);
            #1;
            sel = next_sel;
            clk_en = next_clk_en;
            #1;

            wait(clk0 == 1'b0 && clk1 == 1'b0);
            #1;
            check_output(1'b0, "random both clocks low => clk_out=0");

            if (clk_en == 1'b0) begin
                @(posedge clk0);
                #1;
                check_output(1'b0, "random clk_en=0, after clk0 posedge => clk_out=0");
            end else if (sel == 1'b0) begin
                @(posedge clk0);
                #1;
                check_output(1'b1, "random sel=0, after clk0 posedge => clk_out=1");
            end else begin
                @(posedge clk1);
                #1;
                check_output(1'b1, "random sel=1, after clk1 posedge => clk_out=1");
            end
        end

        // ------------------------------------------------
        // Test 13: Edge case - sel and clk_en change simultaneously
        // ------------------------------------------------
        $display("\n--- Test 13: Simultaneous sel and clk_en change ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "simul: initial sel=0, clk_en=1, clk0 high => clk_out=1");

        @(negedge clk0);
        sel = 1'b1;
        clk_en = 1'b0;
        #1;
        check_output(1'b0, "simul: sel=1, clk_en=0 captured, clk0 low => clk_out=0");

        @(posedge clk0);
        #1;
        check_output(1'b0, "simul: sel=1, clk_en=0, clk0 high => clk_out=0");

        @(negedge clk1);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "simul: sel=0, clk_en=1, clk0 high => clk_out=1");

        // ------------------------------------------------
        // Test 14: Switch at various phases
        // ------------------------------------------------
        $display("\n--- Test 14: Switch at various clock phases ---");
        @(negedge clk0);
        sel = 1'b0;
        clk_en = 1'b1;
        #1;
        repeat(2) @(posedge clk0);

        // Switch sel when clk0 is high, clk1 is low
        @(posedge clk0);
        #2;
        sel = 1'b1;
        #2;
        // clk0 latch not transparent, en0_latch stays 1 until negedge
        check_output(1'b1, "sel=1 during clk0 high, clk_out still=1 (latch not transparent)");

        @(negedge clk0);
        #1;
        check_output(1'b0, "after clk0 negedge captures sel=1, en0=0, clk0 low => clk_out=0");

        // Wait for clk1 negedge to capture sel=1
        @(negedge clk1);
        #1;
        @(posedge clk1);
        #1;
        check_output(1'b1, "sel=1 fully latched, clk1 high => clk_out=1");

        // Switch back when clk1 is high, clk0 is low
        @(posedge clk1);
        #2;
        sel = 1'b0;
        #2;
        check_output(1'b1, "sel=0 during clk1 high, clk_out still=1 (latch not transparent)");

        @(negedge clk1);
        #1;
        check_output(1'b0, "after clk1 negedge captures sel=0, en1=0, clk1 low => clk_out=0");

        @(negedge clk0);
        #1;
        @(posedge clk0);
        #1;
        check_output(1'b1, "sel=0 fully latched, clk0 high => clk_out=1");

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
