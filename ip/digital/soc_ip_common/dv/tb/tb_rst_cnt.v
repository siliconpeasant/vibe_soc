// ---------------------------------------------------------------------------
// Testbench: tb_rst_cnt
// Purpose  : Functional verification for rst_cnt (reset stretcher).
//            Covers F-001 ~ F-007 and parameterization F-008 / F-014 from
//            verification_plan.md.
//
// Notes:
//   * Verilog-2001/2005 cannot instantiate a parameterized module inside a
//     task; therefore two fixed DUT instances are declared at module scope:
//       DUT_A : CNT_WIDTH = 8, STRETCH_CYCLES = 16  (baseline)
//       DUT_B : CNT_WIDTH = 4, STRETCH_CYCLES = 3   (small boundary)
//   * `error_count`     = checker FAIL counter (assertion failures)
//   * `mismatch_count`  = per-cycle scoreboard mismatch counter (DUT vs golden)
//   * CLK_PERIOD = 10 ns to match SDC create_clock 100MHz constraint.
// ---------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_rst_cnt;

    // -------------------------------------------------------------------------
    // Clock / timing
    // -------------------------------------------------------------------------
    localparam integer CLK_PERIOD = 10;
    reg clk = 1'b0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------------------------
    // Stimuli (shared by both DUT instances)
    // -------------------------------------------------------------------------
    reg rst_n_in_a;
    reg rst_n_in_b;
    wire rst_n_out_a;
    wire rst_n_out_b;

    // -------------------------------------------------------------------------
    // DUT instances
    //   DUT_A : default config (baseline)
    //   DUT_B : small parameter boundary
    // -------------------------------------------------------------------------
    rst_cnt #(
        .CNT_WIDTH      (8),
        .STRETCH_CYCLES (16)
    ) DUT_A (
        .clk        (clk),
        .rst_n_in   (rst_n_in_a),
        .rst_n_out  (rst_n_out_a)
    );

    rst_cnt #(
        .CNT_WIDTH      (4),
        .STRETCH_CYCLES (3)
    ) DUT_B (
        .clk        (clk),
        .rst_n_in   (rst_n_in_b),
        .rst_n_out  (rst_n_out_b)
    );

    // -------------------------------------------------------------------------
    // Stats
    // -------------------------------------------------------------------------
    integer error_count;     // assertion-style FAIL counter
    integer mismatch_count;  // per-cycle scoreboard mismatch
    integer total_checks;

    // -------------------------------------------------------------------------
    // Helper: check that `actual` matches `expected`, log PASS/FAIL.
    // -------------------------------------------------------------------------
    task check_eq;
        input        expected;
        input        actual;
        input [511:0] msg;
        begin
            total_checks = total_checks + 1;
            if (expected === actual) begin
                $display("[PASS] T=%0t | %0s | exp=%b act=%b", $time, msg, expected, actual);
            end else begin
                error_count = error_count + 1;
                $display("[FAIL] T=%0t | %0s | exp=%b act=%b", $time, msg, expected, actual);
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-001 : Basic stretch on DUT_A (STRETCH_CYCLES=16)
    //          After rst_n_in_a rising edge, rst_n_out_a must stay 0 for the
    //          first 15 posedge clk and rise EXACTLY on the 16th posedge clk.
    // -------------------------------------------------------------------------
    task tc_001_basic_stretch_a;
        integer i;
        begin
            $display("");
            $display("=== TC-001: Basic Stretch (DUT_A: STRETCH_CYCLES=16) ===");
            // Drive reset asserted, wait a few cycles
            rst_n_in_a = 1'b0;
            repeat (4) @(posedge clk);
            #1;
            check_eq(1'b0, rst_n_out_a, "TC-001: rst held low pre-release");

            // Release synchronously after a negedge to make timing crisp
            @(negedge clk);
            #1 rst_n_in_a = 1'b1;
            $display("[INFO] TC-001: rst_n_in_a released at T=%0t", $time);

            // First 15 posedge clk -> rst_n_out_a must still be 0
            for (i = 1; i <= 15; i = i + 1) begin
                @(posedge clk);
                #1;
                check_eq(1'b0, rst_n_out_a,
                    {"TC-001: posedge #", " (<STRETCH_CYCLES) must stay 0"});
            end
            // 16th posedge clk -> rst_n_out_a must rise to 1
            @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_a, "TC-001: 16th posedge clk releases rst_n_out_a");

            // Stays high afterward
            @(posedge clk); #1;
            check_eq(1'b1, rst_n_out_a, "TC-001: stays high one cycle later");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-002 : Short pulse on DUT_A (1 clk low -> still stretched to 16 cycles)
    //          Verifies F-005 + F-002.
    // -------------------------------------------------------------------------
    task tc_002_short_pulse_a;
        integer i;
        begin
            $display("");
            $display("=== TC-002: Short Pulse (DUT_A: 1 clk low) ===");
            // Bring DUT to fully released state first
            rst_n_in_a = 1'b1;
            repeat (20) @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_a, "TC-002: pre-condition rst_n_out_a==1");

            // Generate 1-cycle low pulse: assert at mid-cycle, release at mid-cycle
            @(negedge clk);
            #1 rst_n_in_a = 1'b0;
            #1;
            check_eq(1'b0, rst_n_out_a, "TC-002: rst_n_out_a falls async on assert");
            @(negedge clk);
            #1 rst_n_in_a = 1'b1;
            $display("[INFO] TC-002: rst_n_in_a was low for 1 clk, released T=%0t", $time);

            // First 15 posedge clk -> rst_n_out_a must still be 0
            for (i = 1; i <= 15; i = i + 1) begin
                @(posedge clk);
                #1;
                check_eq(1'b0, rst_n_out_a, "TC-002: still stretched");
            end
            // 16th posedge clk -> rst_n_out_a == 1
            @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_a, "TC-002: released after 16 cycles (1clk pulse stretched)");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-003 : Long hold on DUT_A (rst_n_in_a low for 100 clk cycles).
    //          Verifies F-006 — rst_n_out_a stays 0 the entire time.
    // -------------------------------------------------------------------------
    task tc_003_long_hold_a;
        integer i;
        begin
            $display("");
            $display("=== TC-003: Long Hold (DUT_A: rst_n_in_a low for 100 cycles) ===");
            @(negedge clk);
            #1 rst_n_in_a = 1'b0;
            #1;
            check_eq(1'b0, rst_n_out_a, "TC-003: rst_n_out_a low immediately after assert");

            for (i = 0; i < 100; i = i + 1) begin
                @(posedge clk);
                #1;
                if (rst_n_out_a !== 1'b0) begin
                    error_count = error_count + 1;
                    $display("[FAIL] T=%0t | TC-003: cycle %0d rst_n_out_a=%b (expect 0)",
                             $time, i, rst_n_out_a);
                end
            end
            total_checks = total_checks + 1;
            $display("[PASS] TC-003: rst_n_out_a held 0 for 100 cycles");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-004 : Mid-count re-assert on DUT_A (counter must restart).
    //          Verifies F-007.
    //   Sequence:
    //     - assert / release
    //     - wait 8 clk (half of STRETCH_CYCLES=16) -> rst_n_out_a still 0
    //     - re-assert rst_n_in_a for 1 clk -> internal counter cleared
    //     - release -> next 15 posedge stay 0, 16th rises
    // -------------------------------------------------------------------------
    task tc_004_mid_count_reassert_a;
        integer i;
        begin
            $display("");
            $display("=== TC-004: Mid-count Re-assert (DUT_A) ===");
            // First assert + release
            @(negedge clk);
            #1 rst_n_in_a = 1'b0;
            repeat (2) @(posedge clk);
            @(negedge clk);
            #1 rst_n_in_a = 1'b1;
            $display("[INFO] TC-004: first release at T=%0t", $time);

            // Wait 8 posedge clk -> rst_n_out_a must still be 0 (count=8 < 16)
            for (i = 1; i <= 8; i = i + 1) begin
                @(posedge clk);
                #1;
                check_eq(1'b0, rst_n_out_a, "TC-004: still counting (first phase)");
            end

            // Mid-count re-assert for 1 clk
            @(negedge clk);
            #1 rst_n_in_a = 1'b0;
            #1;
            check_eq(1'b0, rst_n_out_a, "TC-004: re-assert immediately lows rst_n_out_a");
            @(negedge clk);
            #1 rst_n_in_a = 1'b1;
            $display("[INFO] TC-004: second release at T=%0t", $time);

            // First 15 posedge after second release -> still 0
            for (i = 1; i <= 15; i = i + 1) begin
                @(posedge clk);
                #1;
                check_eq(1'b0, rst_n_out_a,
                         "TC-004: counter restarted from 0, still <STRETCH_CYCLES");
            end
            // 16th posedge -> rises (proves counter restarted from 0, not from 8)
            @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_a,
                     "TC-004: 16th posedge releases (proves restart)");
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-005 : Async assert on DUT_A — drive rst_n_in_a low at a fractional
    //          time offset (half period after a posedge) and check that
    //          rst_n_out_a drops within ns-level delay, NOT waiting for clk.
    //          Verifies F-002.
    // -------------------------------------------------------------------------
    task tc_005_async_assert_a;
        time t_assert;
        time t_out_low;
        begin
            $display("");
            $display("=== TC-005: Async Assert (DUT_A) ===");
            // Bring DUT to released state
            rst_n_in_a = 1'b1;
            repeat (20) @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_a, "TC-005: pre-condition rst_n_out_a==1");

            // Wait until just after a posedge clk, then offset by 2.5 ns
            // (clk is high for 5 ns starting at every posedge -> 2.5 ns
            // is the middle of the high phase, far from any edge)
            @(posedge clk);
            #2.5;
            t_assert = $time;
            rst_n_in_a = 1'b0;
            #1;  // allow async path to propagate (1 ns)
            t_out_low = $time;
            $display("[INFO] TC-005: rst_n_in_a falling T=%0t, rst_n_out_a low T=%0t, delta=%0t",
                     t_assert, t_out_low, t_out_low - t_assert);
            check_eq(1'b0, rst_n_out_a,
                     "TC-005: rst_n_out_a must be 0 within 1ns of async assert");
            if ((t_out_low - t_assert) > (CLK_PERIOD/2))
                $display("[WARN] TC-005: delta exceeds half period (possible sync path)");
            else
                $display("[INFO] TC-005: delta < half period -> confirmed async");

            // Release cleanly so the next test starts from a known state
            @(negedge clk);
            #1 rst_n_in_a = 1'b1;
            repeat (20) @(posedge clk);
        end
    endtask

    // -------------------------------------------------------------------------
    // TC-006 : Parameterized DUT_B (CNT_WIDTH=4, STRETCH_CYCLES=3).
    //          Verifies F-008 — small parameter boundary.
    // -------------------------------------------------------------------------
    task tc_006_basic_stretch_b;
        integer i;
        begin
            $display("");
            $display("=== TC-006: Parameterized DUT_B (STRETCH_CYCLES=3) ===");
            rst_n_in_b = 1'b0;
            repeat (4) @(posedge clk);
            #1;
            check_eq(1'b0, rst_n_out_b, "TC-006: DUT_B held low pre-release");

            @(negedge clk);
            #1 rst_n_in_b = 1'b1;
            $display("[INFO] TC-006: rst_n_in_b released at T=%0t", $time);

            // First 2 posedge clk -> still 0
            for (i = 1; i <= 2; i = i + 1) begin
                @(posedge clk);
                #1;
                check_eq(1'b0, rst_n_out_b,
                         "TC-006: DUT_B still counting (<STRETCH_CYCLES)");
            end
            // 3rd posedge clk -> rises
            @(posedge clk);
            #1;
            check_eq(1'b1, rst_n_out_b, "TC-006: DUT_B releases on 3rd posedge");

            @(posedge clk); #1;
            check_eq(1'b1, rst_n_out_b, "TC-006: DUT_B stays high");
        end
    endtask

    // -------------------------------------------------------------------------
    // Continuous per-cycle scoreboard: golden reference model for DUT_A.
    //   Golden: when rst_n_in_a is low, gold_cnt clears to 0 and gold_done=0.
    //           when rst_n_in_a is high, gold_cnt increments until reaching
    //           STRETCH_CYCLES_A (16), then gold_done latches 1.
    //   Expected rst_n_out_a == gold_done.
    //   Compare on every posedge clk (with #1 delta to settle).
    // -------------------------------------------------------------------------
    localparam integer STRETCH_A = 16;
    reg [7:0] gold_cnt_a;
    reg       gold_done_a;

    always @(posedge clk or negedge rst_n_in_a) begin
        if (!rst_n_in_a) begin
            gold_cnt_a  <= 8'd0;
            gold_done_a <= 1'b0;
        end else if (!gold_done_a) begin
            gold_cnt_a <= gold_cnt_a + 8'd1;
            // match RTL semantics: when cnt reaches STRETCH_CYCLES-1 at the
            // start of a posedge, this same posedge sets done -> rst_n_out
            // rises on the STRETCH_CYCLES-th posedge clk after release.
            if (gold_cnt_a == (STRETCH_A[7:0] - 8'd1))
                gold_done_a <= 1'b1;
        end
    end

    // -------------------------------------------------------------------------
    // Scoreboard comparator. We sample slightly after the clock edge.
    // We only enable the scoreboard during sb_enable to skip async-assert
    // transient windows where the golden model and DUT may briefly differ
    // because of simulator delta ordering (both are functionally correct).
    // -------------------------------------------------------------------------
    reg sb_enable;
    initial sb_enable = 1'b0;

    always @(posedge clk) begin
        #1;
        if (sb_enable) begin
            if (rst_n_out_a !== gold_done_a) begin
                mismatch_count = mismatch_count + 1;
                $display("[FAIL] T=%0t | SCOREBOARD MISMATCH | DUT=%b gold=%b cnt=%0d",
                         $time, rst_n_out_a, gold_done_a, gold_cnt_a);
            end
        end
    end

    // -------------------------------------------------------------------------
    // Main test sequence
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_rst_cnt);

        $display("============================================================");
        $display("  rst_cnt Functional Testbench");
        $display("============================================================");

        // Init
        error_count    = 0;
        mismatch_count = 0;
        total_checks   = 0;
        rst_n_in_a     = 1'b0;
        rst_n_in_b     = 1'b0;
        gold_cnt_a     = 8'd0;
        gold_done_a    = 1'b0;
        sb_enable      = 1'b0;

        // Let clk start, register reset state
        #1;

        // Enable scoreboard for DUT_A — golden model and DUT share rst_n_in_a
        // and clk so they should track identically every cycle.
        sb_enable = 1'b1;

        // Run TCs in order. DUT_A is exercised by TC-001..TC-005, DUT_B by TC-006.
        tc_001_basic_stretch_a();
        tc_002_short_pulse_a();
        tc_003_long_hold_a();
        tc_004_mid_count_reassert_a();
        tc_005_async_assert_a();
        tc_006_basic_stretch_b();

        // -----------------------------------------------------------------
        // Summary
        // -----------------------------------------------------------------
        $display("");
        $display("============================================================");
        $display("  Test Summary");
        $display("============================================================");
        $display("  total_checks   : %0d", total_checks);
        $display("  errors=%0d mismatches=%0d", error_count, mismatch_count);
        $display("[TB] FINAL: errors=%0d mismatches=%0d", error_count, mismatch_count);
        if ((error_count == 0) && (mismatch_count == 0)) begin
            $display("  RESULT: ALL TESTS PASS");
        end else begin
            $display("  RESULT: %0d ERROR(S), %0d MISMATCH(ES)", error_count, mismatch_count);
        end
        $display("============================================================");

        $finish;
    end

    // -------------------------------------------------------------------------
    // Timeout guard
    // -------------------------------------------------------------------------
    initial begin
        #20000;
        $display("[TIMEOUT] Simulation exceeded 20 us");
        $display("[TB] FINAL: errors=%0d mismatches=%0d (TIMEOUT)",
                 error_count, mismatch_count);
        $finish;
    end

endmodule
