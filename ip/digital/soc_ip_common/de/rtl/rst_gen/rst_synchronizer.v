// -----------------------------------------------------------------------------
// Module   : rst_synchronizer
// Function : Async-assert / Sync-release reset synchronizer.
//            异步低有效复位输入,经 STAGES 级 DFF 在 clk 域同步释放后输出。
//            所有同步链 DFF 共用同一根 rst_async_n 做 async active-low clear,
//            第一级 D 端固定 tie-high(1'b1),只有 clk 上升沿才能把 1 逐级推进。
// Author   : SoC RTL Designer Agent
// Version  : 1.0
// -----------------------------------------------------------------------------
module rst_synchronizer #(
    // 同步链 DFF 级数。合法范围 [2,8],默认 2 级。
    parameter STAGES = 2
)(
    input  wire clk,          // 目标时钟域时钟
    input  wire rst_async_n,  // 异步低有效复位输入
    output wire rst_sync_n    // 同步释放的低有效复位输出
);

    // -------------------------------------------------------------------------
    // 同步链寄存器
    //
    // 设计语义:
    //   - 每个 DFF 的 async active-low clear 端都接 rst_async_n
    //     -> rst_async_n=0 时整链被异步拉 0(异步置位)
    //   - 第一级 D 端固定 1'b1(tie-high),其它级 D 端取自前一级 Q
    //   - 输出 rst_sync_n = sync_chain[STAGES-1](最末级 Q)
    //
    // 编码注意:
    //   - 使用 generate-for 拆出 stage[0] 与 stage[i>=1],避免在同一个 always
    //     里写 if (i==0) 这种 elaboration 期判断后还需要保留两种分支的写法
    //   - sync_chain 拆成独立的 DFF,便于综合工具识别为同步链并施加 dont_touch
    // -------------------------------------------------------------------------
    reg [STAGES-1:0] sync_chain;

    // 第一级:D = 1'b1
    always @(posedge clk or negedge rst_async_n) begin
        if (!rst_async_n)
            sync_chain[0] <= 1'b0;
        else
            sync_chain[0] <= 1'b1;
    end

    // 第 2 ~ STAGES 级:D = 前一级 Q
    genvar i;
    generate
        for (i = 1; i < STAGES; i = i + 1) begin : g_sync_stage
            always @(posedge clk or negedge rst_async_n) begin
                if (!rst_async_n)
                    sync_chain[i] <= 1'b0;
                else
                    sync_chain[i] <= sync_chain[i-1];
            end
        end
    endgenerate

    // -------------------------------------------------------------------------
    // 输出
    // -------------------------------------------------------------------------
    assign rst_sync_n = sync_chain[STAGES-1];

endmodule
