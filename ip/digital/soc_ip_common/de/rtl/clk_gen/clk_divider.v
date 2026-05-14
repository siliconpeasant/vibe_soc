module clk_divider #(
    parameter DIV_WIDTH = 8
)(
    input              clk,
    input              rst_n,
    input  [DIV_WIDTH-1:0] div_ratio,    // 同步输入分频系数
    output reg         clk_out
);

    // -------------------------------------------------------------------------
    // 分频系数变化检测：同步输入，直接采样，变化时清零计数器
    // -------------------------------------------------------------------------
    reg [DIV_WIDTH-1:0] div_ratio_sync;
    reg [DIV_WIDTH-1:0] div_ratio_prev;
    wire div_change;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            div_ratio_sync <= 'd0;
            div_ratio_prev <= 'd0;
        end else begin
            div_ratio_prev <= div_ratio_sync;
            div_ratio_sync <= div_ratio;
        end
    end

    assign div_change = (div_ratio_sync != div_ratio_prev);

    // -------------------------------------------------------------------------
    // 分频系数解析
    // 0 : 输出常 0
    // 1 : 输出直通 clk
    // >= 2 : 分频输出
    // -------------------------------------------------------------------------
    wire [DIV_WIDTH-1:0] half_div = div_ratio_sync >> 1;
    wire is_odd = div_ratio_sync[0];

    // -------------------------------------------------------------------------
    // 正沿计数器与翻转信号（奇偶分频共用）
    // -------------------------------------------------------------------------
    reg [DIV_WIDTH-1:0] cnt_p;
    reg clk_p;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt_p <= 'd0;
            clk_p <= 1'b0;
        end else if (div_change || div_ratio_sync <= 1) begin
            cnt_p <= 'd0;
            clk_p <= 1'b0;
        end else begin
            if (cnt_p >= div_ratio_sync - 1)
                cnt_p <= 'd0;
            else
                cnt_p <= cnt_p + 1'b1;

            if (cnt_p == half_div - 1 || cnt_p == div_ratio_sync - 1)
                clk_p <= ~clk_p;
        end
    end

    // -------------------------------------------------------------------------
    // 负沿计数器与翻转信号（仅奇数分频需要，用于构造 50% 占空比）
    // -------------------------------------------------------------------------
    reg [DIV_WIDTH-1:0] cnt_n;
    reg clk_n;

    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt_n <= 'd0;
            clk_n <= 1'b0;
        end else if (div_change || div_ratio_sync <= 1) begin
            cnt_n <= 'd0;
            clk_n <= 1'b0;
        end else begin
            if (cnt_n >= div_ratio_sync - 1)
                cnt_n <= 'd0;
            else
                cnt_n <= cnt_n + 1'b1;

            if (cnt_n == half_div - 1 || cnt_n == div_ratio_sync - 1)
                clk_n <= ~clk_n;
        end
    end

    // -------------------------------------------------------------------------
    // 输出选择
    // -------------------------------------------------------------------------
    always @(*) begin
        if (div_ratio_sync == 0)
            clk_out = 1'b0;
        else if (div_ratio_sync == 1)
            clk_out = clk;
        else if (!is_odd)
            clk_out = clk_p;          // 偶数分频
        else
            clk_out = clk_p | clk_n;  // 奇数分频：正沿/负沿波形相或得到 50% 占空比
    end

endmodule
