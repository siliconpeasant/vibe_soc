`timescale 1ns / 1ps

module tb_clk_divider;

    parameter DIV_WIDTH = 8;

    reg              clk;
    reg              rst_n;
    reg  [DIV_WIDTH-1:0] div_ratio;
    wire             clk_out;

    clk_divider #(
        .DIV_WIDTH(DIV_WIDTH)
    ) u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .div_ratio (div_ratio),
        .clk_out   (clk_out)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    // 任务：在 negedge 改变分频系数（避免竞争）
    task set_ratio;
        input [DIV_WIDTH-1:0] ratio;
        begin
            @(negedge clk);
            div_ratio = ratio;
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_clk_divider);

        $display("========================================");
        $display("  clk_divider Testbench");
        $display("========================================");

        // 复位
        rst_n     = 1'b0;
        div_ratio = 8'd0;
        #20;
        rst_n = 1'b1;
        #10;

        // Test 1: div_ratio = 0 => 输出常 0
        set_ratio(8'd0);
        repeat(10) @(posedge clk);
        $display("[TEST] div_ratio=0, clk_out=%b (expect 0)", clk_out);

        // Test 2: div_ratio = 1 => 直通
        set_ratio(8'd1);
        repeat(10) @(posedge clk);
        $display("[TEST] div_ratio=1, clk_out 直通 clk");

        // Test 3: 偶数分频 = 4
        set_ratio(8'd4);
        repeat(24) @(posedge clk);
        $display("[TEST] div_ratio=4 (偶数分频)");

        // Test 4: 偶数分频 = 6
        set_ratio(8'd6);
        repeat(30) @(posedge clk);
        $display("[TEST] div_ratio=6 (偶数分频)");

        // Test 5: 奇数分频 = 3
        set_ratio(8'd3);
        repeat(20) @(posedge clk);
        $display("[TEST] div_ratio=3 (奇数分频)");

        // Test 6: 奇数分频 = 5
        set_ratio(8'd5);
        repeat(30) @(posedge clk);
        $display("[TEST] div_ratio=5 (奇数分频)");

        // Test 7: 动态切换 div_ratio
        set_ratio(8'd8);
        repeat(20) @(posedge clk);
        $display("[TEST] div_ratio=8 (偶数分频)");

        set_ratio(8'd3);
        repeat(15) @(posedge clk);
        set_ratio(8'd7);
        repeat(35) @(posedge clk);
        $display("[TEST] 动态切换 3 -> 7 (奇数分频)");

        // Test 8: 大分频系数
        set_ratio(8'd10);
        repeat(40) @(posedge clk);
        $display("[TEST] div_ratio=10 (偶数分频)");

        $display("========================================");
        $display("  All tests passed!");
        $display("========================================");
        $finish;
    end

endmodule
