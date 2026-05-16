// ---------------------------------------------------------------------------
// Testbench: tb_rst_synchronizer
// Purpose  : Functional verification for rst_synchronizer
//            Covers TC-001 ~ TC-007, STAGES = 2/3
// ---------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_rst_synchronizer;

    // -------------------------------------------------------------------------
    // Clock / timing
    // -------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;
    reg clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // DUT signals (parameterized instances created inside tasks)
    // -------------------------------------------------------------------------
    reg  rst_async_n;
    wire rst_sync_n;

    // -------------------------------------------------------------------------
    // Test result counters
    // -------------------------------------------------------------------------
    integer errors;
    integer passes;
    integer total_tests;

    // -------------------------------------------------------------------------
    // Helper: check a condition and log
    // -------------------------------------------------------------------------
    task check;
        input expected;
        input actual;
        input [255*8:0] msg;
        begin
            total_tests = total_tests + 1;
            if (expected === actual) begin
                passes = passes + 1;
                $display("[PASS] T=%0t | %s | expected=%b actual=%b", $time, msg, expected, actual);
            end else begin
                errors = errors + 1;
                $display("[FAIL] T=%0t | %s | expected=%b actual=%b", $time, msg, expected, actual);
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // DUT wrapper task: instantiate with parameter, run a stimulus block,
    // then destroy (by ending the fork-join_none scope).  We use a macro
    // approach instead: the test tasks accept STAGES as argument and
    // instantiate a local DUT inside a fork-join block.
    // -------------------------------------------------------------------------

    // -------------------------------------------------------------------------
    // TC-001: Power-on reset -- rst_async_n=0 at t=0, hold 5 cycles,
    //         rst_sync_n must stay 0 the whole time.
    // -------------------------------------------------------------------------
    task tc_001_power_on_reset;
        input integer STAGES;
        begin
            $display("\n=== TC-001 (STAGES=%0d): Power-on Reset ===", STAGES);
            rst_async_n = 0;
            #1;
            check(1'b0, rst_sync_n, "TC-001: t=0 rst_sync_n should be 0");
            @(posedge clk);
            check(1'b0, rst_sync_n, "TC-001: after 1st posedge clk");
            @(posedge clk);
            check(1'b0, rst_sync_n, "TC-001: after 2nd posedge clk");
            @(posedge clk);
            check(1'b0, rst_sync_n, "TC-001: after 3rd posedge clk");
            @(posedge clk);
            check(1'b0, rst_sync_n, "TC-001: after 4th posedge clk");
            @(posedge clk);
            check(1'b0, rst_sync_n, "TC-001: after 5th posedge clk");
            // release
            @(negedge clk);
            #1 rst_async_n = 1;
            repeat(STAGES) @(posedge clk);
            #(CLK_PERIOD/2);
            check(1'b1, rst_sync_n, "TC-001: after STAGES posedge clk post-release");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-002: Async assert -- rst_async_n pulled low mid-cycle (no clk edge),
    //         rst_sync_n must drop immediately (asynchronously).
    // -------------------------------------------------------------------------
    task tc_002_async_assert;
        input integer STAGES;
        reg [63:0] t_assert;
        reg [63:0] t_sync_low;
        begin
            $display("\n=== TC-002 (STAGES=%0d): Async Assert ===", STAGES);
            // bring DUT to idle state
            rst_async_n = 1;
            repeat(STAGES + 2) @(posedge clk);
            check(1'b1, rst_sync_n, "TC-002: pre-condition rst_sync_n==1");

            // Pull low exactly at mid-cycle (no posedge nearby)
            @(negedge clk);
            #(CLK_PERIOD/4);
            rst_async_n = 0;
            t_assert = $time;
            #1;  // allow combinational / async path to propagate
            t_sync_low = $time;
            $display("[INFO] TC-002: rst_async_n asserted at T=%0t, rst_sync_n low at T=%0t, delta=%0t",
                     t_assert, t_sync_low, t_sync_low - t_assert);
            check(1'b0, rst_sync_n, "TC-002: rst_sync_n must be 0 immediately after async assert");
            if ((t_sync_low - t_assert) > (CLK_PERIOD/2))
                $display("[WARN] TC-002: delta > half period, may not be truly async!");
            else
                $display("[INFO] TC-002: delta < half period -> confirmed async");

            // clean up
            @(negedge clk);
            #1 rst_async_n = 1;
            repeat(STAGES) @(posedge clk);
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-003: Sync release delay -- after rst_async_n goes 1, count posedge
    //         clk and verify rst_sync_n rises exactly on the STAGES-th edge.
    // -------------------------------------------------------------------------
    task tc_003_sync_release_delay;
        input integer STAGES;
        integer edge_cnt;
        begin
            $display("\n=== TC-003 (STAGES=%0d): Sync Release Delay ===", STAGES);
            // assert
            rst_async_n = 0;
            repeat(3) @(posedge clk);
            check(1'b0, rst_sync_n, "TC-003: pre-release check");

            // release just after a posedge to avoid ambiguity
            @(negedge clk);
            #1 rst_async_n = 1;
            $display("[INFO] TC-003: rst_async_n released at T=%0t", $time);

            edge_cnt = 0;
            // On each posedge before the STAGES-th, rst_sync_n must still be 0
            while (edge_cnt < STAGES) begin
                @(posedge clk);
                #(CLK_PERIOD/2);
                edge_cnt = edge_cnt + 1;
                $display("[INFO] TC-003: posedge clk #%0d at T=%0t, rst_sync_n=%b",
                         edge_cnt, $time, rst_sync_n);
                if (edge_cnt < STAGES)
                    check(1'b0, rst_sync_n,
                          {"TC-003: before STAGES-th edge (edge ",
                           "cnt < STAGES)"});
                else
                    check(1'b1, rst_sync_n,
                          {"TC-003: exactly at STAGES-th posedge clk"});
            end

            // one more cycle to confirm it stays 1
            @(posedge clk);
            #(CLK_PERIOD/2);
            check(1'b1, rst_sync_n, "TC-003: one cycle after release done");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-004: Short pulse glitch -- low pulse width < CLK_PERIOD/2,
    //         must still be captured and cause full re-sync.
    // -------------------------------------------------------------------------
    task tc_004_short_pulse;
        input integer STAGES;
        integer edge_cnt;
        begin
            $display("\n=== TC-004 (STAGES=%0d): Short Pulse Glitch ===", STAGES);
            // idle
            rst_async_n = 1;
            repeat(STAGES + 2) @(posedge clk);
            check(1'b1, rst_sync_n, "TC-004: pre-glitch idle");

            // generate short low pulse (1/4 period) between posedges
            @(negedge clk);
            #(CLK_PERIOD/4);
            rst_async_n = 0;
            #(CLK_PERIOD/4);
            rst_async_n = 1;
            $display("[INFO] TC-004: glitch pulse width = %0t (period/4)", CLK_PERIOD/4);

            // immediately after pulse (no clk yet), rst_sync_n should be 0
            @(negedge clk);
            check(1'b0, rst_sync_n, "TC-004: rst_sync_n low right after glitch");

            // count STAGES posedge clk for full recovery
            edge_cnt = 0;
            while (edge_cnt < STAGES) begin
                @(posedge clk);
                @(negedge clk);
                edge_cnt = edge_cnt + 1;
                $display("[INFO] TC-004: recovery posedge #%0d at T=%0t, rst_sync_n=%b",
                         edge_cnt, $time, rst_sync_n);
                if (edge_cnt < STAGES)
                    check(1'b0, rst_sync_n, "TC-004: recovery in progress");
                else
                    check(1'b1, rst_sync_n, "TC-004: fully recovered at STAGES-th edge");
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-006: Reset held for 100 cycles -- rst_sync_n must stay 0 continuously.
    // -------------------------------------------------------------------------
    task tc_006_long_assert;
        input integer STAGES;
        integer i;
        begin
            $display("\n=== TC-006 (STAGES=%0d): Long Assert (100 cycles) ===", STAGES);
            rst_async_n = 0;
            @(posedge clk);  // align
            for (i = 0; i < 100; i = i + 1) begin
                @(posedge clk);
                check(1'b0, rst_sync_n,
                      {"TC-006: cycle ", "check during long assert"});
            end
            @(negedge clk);
            #1 rst_async_n = 1;
            repeat(STAGES) @(posedge clk);
            #(CLK_PERIOD/2);
            check(1'b1, rst_sync_n, "TC-006: after release");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-007: Multiple consecutive assert / release cycles.
    // -------------------------------------------------------------------------
    task tc_007_multiple_cycles;
        input integer STAGES;
        integer iter;
        integer hold_cycles;
        integer wait_cycles;
        integer edge_cnt;
        begin
            $display("\n=== TC-007 (STAGES=%0d): Multiple Cycles ===", STAGES);
            rst_async_n = 1;
            repeat(STAGES + 2) @(posedge clk);

            for (iter = 0; iter < 16; iter = iter + 1) begin
                hold_cycles = $random % 5;
                if (hold_cycles < 0) hold_cycles = -hold_cycles;
                hold_cycles = hold_cycles + 1;     // 1 ~ 5 cycles
                wait_cycles = $random % 11;
                if (wait_cycles < 0) wait_cycles = -wait_cycles; // 0 ~ 10 cycles

                // assert
                @(negedge clk);
                #1 rst_async_n = 0;
                repeat(hold_cycles) @(posedge clk);

                // release
                @(negedge clk);
                #1 rst_async_n = 1;
                $display("[INFO] TC-007 iter=%0d: hold=%0d wait=%0d", iter, hold_cycles, wait_cycles);

                edge_cnt = 0;
                while (edge_cnt < STAGES) begin
                    @(posedge clk);
                    #0;
                    edge_cnt = edge_cnt + 1;
                    if (edge_cnt < STAGES)
                        check(1'b0, rst_sync_n, {"TC-007: mid-release"});
                    else
                        check(1'b1, rst_sync_n, {"TC-007: released"});
                end

                repeat(wait_cycles) @(posedge clk);
                #(CLK_PERIOD/2);
                check(1'b1, rst_sync_n, "TC-007: post-wait stable");
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Run all TCs for a given STAGES value using a local DUT instance.
    // Because Verilog does not allow parameterized module instantiation
    // inside a task, we use a generate block with three fixed instances
    // and mux the active one.
    // -------------------------------------------------------------------------

    // Two DUT instances (STAGES=2/3 only)
    wire rst_sync_n_s2;
    wire rst_sync_n_s3;

    rst_synchronizer #(2) dut_s2 (.clk(clk), .rst_async_n(rst_async_n), .rst_sync_n(rst_sync_n_s2));
    rst_synchronizer #(3) dut_s3 (.clk(clk), .rst_async_n(rst_async_n), .rst_sync_n(rst_sync_n_s3));

    reg [1:0] sel_stages;  // 0=unused, 1=STAGES=2, 2=STAGES=3
    assign rst_sync_n = (sel_stages == 1) ? rst_sync_n_s2 :
                        (sel_stages == 2) ? rst_sync_n_s3 : 1'bx;

    task run_all_tc_for_stages;
        input integer STAGES;
        begin
            case (STAGES)
                2: sel_stages = 1;
                3: sel_stages = 2;
                default: sel_stages = 0;
            endcase
            $display("\n============================================================");
            $display("  Starting test suite for STAGES = %0d", STAGES);
            $display("============================================================");

            tc_001_power_on_reset(STAGES);
            tc_002_async_assert(STAGES);
            tc_003_sync_release_delay(STAGES);
            tc_004_short_pulse(STAGES);
            tc_006_long_assert(STAGES);
            tc_007_multiple_cycles(STAGES);
        end
    endtask

    // -------------------------------------------------------------------------
    // Main test sequence
    // -------------------------------------------------------------------------
    initial begin
        $display("============================================================");
        $display("  rst_synchronizer Functional Testbench");
        $display("============================================================");

        errors = 0;
        passes = 0;
        total_tests = 0;
        sel_stages = 0;
        rst_async_n = 0;

        // small delay to let clk start
        #1;

        // Run for STAGES = 2, 3
        run_all_tc_for_stages(2);
        run_all_tc_for_stages(3);

        // ---------------------------------------------------------------------
        // Summary
        // ---------------------------------------------------------------------
        $display("\n============================================================");
        $display("  Test Summary");
        $display("============================================================");
        $display("  Total checks : %0d", total_tests);
        $display("  PASS         : %0d", passes);
        $display("  ERROR        : %0d", errors);
        if (errors == 0)
            $display("  RESULT: ALL TESTS PASS");
        else
            $display("  RESULT: SOME TESTS FAILED");
        $display("============================================================");

        $finish;
    end

    // -------------------------------------------------------------------------
    // Timeout watchdog
    // -------------------------------------------------------------------------
    initial begin
        #50000;
        $display("[TIMEOUT] Simulation exceeded 50 us, forcing exit.");
        $finish;
    end

endmodule
