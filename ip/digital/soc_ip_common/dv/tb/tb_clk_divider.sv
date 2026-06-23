`timescale 1ns / 1ps

module tb_clk_divider;

    localparam integer DIV_WIDTH       = 8;
    localparam integer SMALL_DIV_WIDTH = 4;
    localparam time    HALF_PERIOD     = 5;
    localparam time    FULL_PERIOD     = 2 * HALF_PERIOD;

    reg                         clk;
    reg                         rst_n;
    reg  [DIV_WIDTH-1:0]        div_ratio;
    wire                        clk_out;
    reg                         rst_n_small;
    reg  [SMALL_DIV_WIDTH-1:0]  div_ratio_small;
    wire                        clk_out_small;

    integer errors;
    integer test_count;
    integer random_seed;
    integer lfsr;

    clk_divider #(
        .DIV_WIDTH(DIV_WIDTH)
    ) u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .div_ratio (div_ratio),
        .clk_out   (clk_out)
    );

    clk_divider #(
        .DIV_WIDTH(SMALL_DIV_WIDTH)
    ) u_dut_small (
        .clk       (clk),
        .rst_n     (rst_n_small),
        .div_ratio (div_ratio_small),
        .clk_out   (clk_out_small)
    );

    initial begin
        clk = 1'b0;
        forever #(HALF_PERIOD) clk = ~clk;
    end

    task begin_test;
        input [511:0] name;
        begin
            test_count = test_count + 1;
            $display("[TEST %0d] %0s", test_count, name);
        end
    endtask

    task record_error;
        input [511:0] msg;
        begin
            errors = errors + 1;
            $display("[ERROR] %0t %0s", $time, msg);
        end
    endtask

    task check_known_main;
        input [511:0] ctx;
        begin
            if (clk_out !== 1'b0 && clk_out !== 1'b1) begin
                record_error({"clk_out is X/Z during ", ctx});
            end
        end
    endtask

    task check_known_small;
        input [511:0] ctx;
        begin
            if (clk_out_small !== 1'b0 && clk_out_small !== 1'b1) begin
                record_error({"clk_out_small is X/Z during ", ctx});
            end
        end
    endtask

    task set_ratio_main;
        input [DIV_WIDTH-1:0] ratio;
        begin
            @(negedge clk);
            div_ratio = ratio;
        end
    endtask

    task set_ratio_small;
        input [SMALL_DIV_WIDTH-1:0] ratio;
        begin
            @(negedge clk);
            div_ratio_small = ratio;
        end
    endtask

    task reset_main;
        begin
            rst_n = 1'b0;
            #(HALF_PERIOD);
            if (clk_out !== 1'b0) begin
                record_error("reset did not force clk_out low");
            end
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1;
            check_known_main("reset release");
        end
    endtask

    task reset_small;
        begin
            rst_n_small = 1'b0;
            #(HALF_PERIOD);
            if (clk_out_small !== 1'b0) begin
                record_error("reset did not force clk_out_small low");
            end
            repeat (2) @(posedge clk);
            rst_n_small = 1'b1;
            @(posedge clk);
            #1;
            check_known_small("small reset release");
        end
    endtask

    task check_force_low_main;
        input integer cycles;
        input [511:0] ctx;
        integer i;
        begin
            repeat (2) @(posedge clk);
            for (i = 0; i < cycles * 2; i = i + 1) begin
                @(clk);
                #1;
                check_known_main(ctx);
                if (clk_out !== 1'b0) begin
                    record_error({"clk_out toggled in force-low mode during ", ctx});
                end
            end
        end
    endtask

    task check_bypass_main;
        input integer half_cycles;
        integer i;
        begin
            repeat (2) @(posedge clk);
            for (i = 0; i < half_cycles; i = i + 1) begin
                @(clk);
                #1;
                check_known_main("bypass");
                if (clk_out !== clk) begin
                    record_error("div_ratio=1 bypass does not follow clk");
                end
            end
        end
    endtask

    task wait_for_divided_restart_main;
        input integer ratio;
        begin
            @(posedge clk);
            #1;
            check_known_main("divided restart");
            if (clk_out !== 1'b0) begin
                record_error("divided mode did not restart from low phase");
            end
            wait (clk_out === 1'b1);
        end
    endtask

    task check_divided_main;
        input integer ratio;
        input integer edge_count;
        input [511:0] ctx;
        integer i;
        time last_edge;
        time delta;
        time expected_delta;
        begin
            expected_delta = ratio * HALF_PERIOD;
            wait_for_divided_restart_main(ratio);
            last_edge = $time;
            for (i = 0; i < edge_count; i = i + 1) begin
                @(clk_out);
                check_known_main(ctx);
                delta = $time - last_edge;
                if (delta !== expected_delta) begin
                    record_error({"wrong divided edge interval during ", ctx});
                    $display("        ratio=%0d expected_delta=%0t actual_delta=%0t", ratio, expected_delta, delta);
                end
                last_edge = $time;
                #1;
            end
        end
    endtask

    task check_divided_small;
        input integer ratio;
        input integer edge_count;
        input [511:0] ctx;
        integer i;
        time last_edge;
        time delta;
        time expected_delta;
        begin
            expected_delta = ratio * HALF_PERIOD;
            @(posedge clk);
            #1;
            check_known_small("small divided restart");
            if (clk_out_small !== 1'b0) begin
                record_error("small divider did not restart from low phase");
            end
            wait (clk_out_small === 1'b1);
            last_edge = $time;
            for (i = 0; i < edge_count; i = i + 1) begin
                @(clk_out_small);
                check_known_small(ctx);
                delta = $time - last_edge;
                if (delta !== expected_delta) begin
                    record_error({"wrong small divided edge interval during ", ctx});
                    $display("        ratio=%0d expected_delta=%0t actual_delta=%0t", ratio, expected_delta, delta);
                end
                last_edge = $time;
                #1;
            end
        end
    endtask

    task check_reset_during_active;
        input integer ratio;
        begin
            set_ratio_main(ratio[DIV_WIDTH-1:0]);
            wait_for_divided_restart_main(ratio);
            #(HALF_PERIOD + 2);
            rst_n = 1'b0;
            #1;
            if (clk_out !== 1'b0) begin
                record_error("reset during active divide did not force low");
            end
            repeat (2) @(posedge clk);
            rst_n = 1'b1;
            check_divided_main(ratio, 4, "post mid-period reset");
        end
    endtask

    task run_seeded_random;
        integer i;
        integer ratio;
        begin
            lfsr = random_seed;
            for (i = 0; i < 8; i = i + 1) begin
                lfsr = {lfsr[30:0], lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
                ratio = ((lfsr & 32'h7fffffff) % 10);
                if (ratio < 2) begin
                    set_ratio_main(ratio[DIV_WIDTH-1:0]);
                    if (ratio == 0) begin
                        check_force_low_main(4, "seeded random ratio 0");
                    end else begin
                        check_bypass_main(8);
                    end
                end else begin
                    set_ratio_main(ratio[DIV_WIDTH-1:0]);
                    check_divided_main(ratio, 3, "seeded random divided ratio");
                end
            end
        end
    endtask

    initial begin
        errors          = 0;
        test_count      = 0;
        random_seed     = 32'h1bad_c0de;
        lfsr            = random_seed;
        rst_n           = 1'b0;
        rst_n_small     = 1'b0;
        div_ratio       = {DIV_WIDTH{1'b0}};
        div_ratio_small = {SMALL_DIV_WIDTH{1'b0}};

        $dumpfile("wave.vcd");
        $dumpvars(0, tb_clk_divider);

        begin_test("reset forces low");
        reset_main();
        reset_small();

        begin_test("div_ratio 0 force low");
        set_ratio_main(8'd0);
        check_force_low_main(12, "ratio 0");

        begin_test("div_ratio 1 bypass");
        set_ratio_main(8'd1);
        check_bypass_main(16);

        begin_test("divide-by-2");
        set_ratio_main(8'd2);
        check_divided_main(2, 8, "divide by 2");

        begin_test("even ratios 4 6 8");
        set_ratio_main(8'd4);
        check_divided_main(4, 8, "divide by 4");
        set_ratio_main(8'd6);
        check_divided_main(6, 8, "divide by 6");
        set_ratio_main(8'd8);
        check_divided_main(8, 8, "divide by 8");

        begin_test("odd ratios 3 5 7 9");
        set_ratio_main(8'd3);
        check_divided_main(3, 8, "divide by 3");
        set_ratio_main(8'd5);
        check_divided_main(5, 8, "divide by 5");
        set_ratio_main(8'd7);
        check_divided_main(7, 8, "divide by 7");
        set_ratio_main(8'd9);
        check_divided_main(9, 8, "divide by 9");

        begin_test("practical maximum small-width ratio");
        set_ratio_small(4'd15);
        check_divided_small(15, 5, "small divide by 15");

        begin_test("dynamic ratio class transitions");
        set_ratio_main(8'd0);
        check_force_low_main(4, "dynamic divided to force-low");
        set_ratio_main(8'd1);
        check_bypass_main(8);
        set_ratio_main(8'd4);
        check_divided_main(4, 4, "dynamic bypass to even");
        set_ratio_main(8'd5);
        check_divided_main(5, 4, "dynamic even to odd");
        set_ratio_main(8'd8);
        check_divided_main(8, 4, "dynamic odd to even");
        set_ratio_main(8'd3);
        check_divided_main(3, 4, "dynamic even to odd second");

        begin_test("reset during active divide");
        check_reset_during_active(6);
        check_reset_during_active(5);

        begin_test("seeded random legal ratios");
        run_seeded_random();

        if (errors == 0) begin
            $display("RESULT: ALL TESTS PASS");
        end else begin
            $display("RESULT: TESTS FAILED");
        end
        $finish;
    end

endmodule
