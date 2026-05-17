// -----------------------------------------------------------------------------
// Module   : rst_cnt
// Function : Reset stretcher with async-assert / sync-deassert semantics.
//            rst_n_in 拉低时,内部计数器与 done 标志被异步清零,rst_n_out
//            立刻变 0;rst_n_in 释放后,在 clk 域累计 STRETCH_CYCLES 个
//            posedge 才把 rst_n_out 拉高(同步释放,延迟释放窗口)。
//            计数中途若 rst_n_in 再次被 assert,所有 DFF 被异步清零并
//            从头开始计数。
// Author   : SoC RTL Designer Agent
// Version  : 1.0
// -----------------------------------------------------------------------------

module rst_cnt #(
    // 内部计数器位宽,合法范围 [1, 32],默认 8 bit。
    parameter integer CNT_WIDTH      = 8,
    // rst_n_in 释放后到 rst_n_out 释放之间的 clk 周期数,
    // 合法范围 [1, 2**CNT_WIDTH - 1],默认 16。
    parameter integer STRETCH_CYCLES = 16
)(
    input  wire clk,        // 工作时钟,上升沿驱动
    input  wire rst_n_in,   // 异步低有效复位输入(异步 assert / 同步 deassert)
    output wire rst_n_out   // 延迟释放的低有效复位输出
);

    // -------------------------------------------------------------------------
    // Elaboration-time 参数合法性检查
    //   STRETCH_CYCLES 必须 <= 2**CNT_WIDTH - 1,否则计数器位宽承载不下终值。
    //   Verilog-2005 兼容:用 initial + $fatal,综合工具会跳过 initial 块,
    //   不会引入硬件。
    // -------------------------------------------------------------------------
    // verilator lint_off WIDTH
    localparam [CNT_WIDTH-1:0] STRETCH_CYCLES_TERM   = STRETCH_CYCLES[CNT_WIDTH-1:0];
    // cnt_reg 达到 STRETCH_CYCLES_TERM_M1 时,下一个 posedge 将 done_reg 置 1,
    // 该 posedge 也是 rst_n_in 释放后的第 STRETCH_CYCLES 个 posedge clk,
    // 与 spec "释放后第 STRETCH_CYCLES 个 posedge clk 上变 1" 严格一致。
    localparam [CNT_WIDTH-1:0] STRETCH_CYCLES_TERM_M1 = STRETCH_CYCLES_TERM - {{(CNT_WIDTH-1){1'b0}}, 1'b1};
    // verilator lint_on WIDTH

    initial begin
        if (STRETCH_CYCLES < 1) begin
            $display("rst_cnt: STRETCH_CYCLES (%0d) must be >= 1", STRETCH_CYCLES);
            $fatal;
        end
        if (STRETCH_CYCLES > ((1 << CNT_WIDTH) - 1)) begin
            $display("rst_cnt: STRETCH_CYCLES (%0d) exceeds CNT_WIDTH (%0d) capacity (%0d)",
                     STRETCH_CYCLES, CNT_WIDTH, (1 << CNT_WIDTH) - 1);
            $fatal;
        end
    end

    // -------------------------------------------------------------------------
    // 内部寄存器
    //   - cnt_reg : CNT_WIDTH-bit 计数器,async active-low clear by rst_n_in
    //   - done_reg: 1-bit 标志,计数达到终值后置 1 并自锁,
    //               async active-low clear by rst_n_in
    //   两者共用同一根 rst_n_in 做异步置位 -> 异步 assert 语义。
    // -------------------------------------------------------------------------
    reg [CNT_WIDTH-1:0] cnt_reg;
    reg                 done_reg;

    wire cnt_at_term_m1 = (cnt_reg == STRETCH_CYCLES_TERM_M1);

    // -------------------------------------------------------------------------
    // 计数器:rst_n_in=0 异步清零;rst_n_in=1 时,在 !done_reg 期间每 clk +1,
    //         达到终值后停在 STRETCH_CYCLES_TERM(saturating),保证不会回卷。
    // -------------------------------------------------------------------------
    always @(posedge clk or negedge rst_n_in) begin
        if (!rst_n_in) begin
            cnt_reg <= {CNT_WIDTH{1'b0}};
        end else if (!done_reg) begin
            cnt_reg <= cnt_reg + {{(CNT_WIDTH-1){1'b0}}, 1'b1};
        end else begin
            cnt_reg <= cnt_reg; // hold at terminal value
        end
    end

    // -------------------------------------------------------------------------
    // done_reg:rst_n_in=0 异步清零;计数到达终值时 set,并通过自反馈锁住。
    //          一旦 done_reg=1,rst_n_out 即释放;直到下次 rst_n_in 拉低才清零。
    // -------------------------------------------------------------------------
    always @(posedge clk or negedge rst_n_in) begin
        if (!rst_n_in) begin
            done_reg <= 1'b0;
        end else if (cnt_at_term_m1) begin
            done_reg <= 1'b1;
        end else begin
            done_reg <= done_reg; // self-hold
        end
    end

    // -------------------------------------------------------------------------
    // 输出:rst_n_out = done_reg
    //   rst_n_in=0 时由异步路径(done_reg async clear)立即拉低 -> 异步 assert
    //   rst_n_in=1 后由 clk 同步路径在 STRETCH_CYCLES 周期后拉高 -> 同步 deassert
    // -------------------------------------------------------------------------
    assign rst_n_out = done_reg;

endmodule
