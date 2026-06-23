module clk_divider #(
    parameter DIV_WIDTH = 8
)(
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire [DIV_WIDTH-1:0] div_ratio,
    output reg                  clk_out
);

    localparam [DIV_WIDTH-1:0] RATIO_ZERO = {DIV_WIDTH{1'b0}};

    reg [DIV_WIDTH-1:0] div_ratio_q;
    reg [DIV_WIDTH-1:0] cnt_p;
    reg [DIV_WIDTH-1:0] cnt_n;
    reg                 clk_p;
    reg                 clk_n;
    reg                 restart_n;

    function [DIV_WIDTH-1:0] make_ratio_one;
        input unused;
        begin
            make_ratio_one    = {DIV_WIDTH{1'b0}};
            make_ratio_one[0] = 1'b1;
        end
    endfunction

    wire [DIV_WIDTH-1:0] ratio_one = make_ratio_one(1'b0);

    wire ratio_change = (div_ratio != div_ratio_q);
    wire ratio_zero   = (div_ratio_q == RATIO_ZERO);
    wire ratio_is_one = (div_ratio_q == ratio_one);
    wire ratio_active = (div_ratio_q >  ratio_one);
    wire ratio_odd    = div_ratio_q[0];

    wire [DIV_WIDTH-1:0] even_limit = div_ratio_q >> 1;
    wire [DIV_WIDTH-1:0] odd_low_limit =
        (div_ratio_q >> 1) + ratio_one;
    wire [DIV_WIDTH-1:0] odd_high_limit = div_ratio_q >> 1;

    // -------------------------------------------------------------------------
    // Positive-edge ratio sampling and divider phase.  A sampled ratio change
    // clears the phase state before the new ratio is used for division.
    // -------------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            div_ratio_q <= RATIO_ZERO;
            cnt_p       <= RATIO_ZERO;
            clk_p       <= 1'b0;
            restart_n   <= 1'b1;
        end else begin
            div_ratio_q <= div_ratio;
            restart_n   <= ratio_change || (div_ratio <= ratio_one);

            if (ratio_change || (div_ratio <= ratio_one)) begin
                cnt_p <= RATIO_ZERO;
                clk_p <= 1'b0;
            end else if (!ratio_odd) begin
                if (cnt_p == (even_limit - ratio_one)) begin
                    cnt_p <= RATIO_ZERO;
                    clk_p <= ~clk_p;
                end else begin
                    cnt_p <= cnt_p + ratio_one;
                end
            end else if (!clk_p) begin
                if (cnt_p == (odd_low_limit - ratio_one)) begin
                    cnt_p <= RATIO_ZERO;
                    clk_p <= 1'b1;
                end else begin
                    cnt_p <= cnt_p + ratio_one;
                end
            end else begin
                if (cnt_p == (odd_high_limit - ratio_one)) begin
                    cnt_p <= RATIO_ZERO;
                    clk_p <= 1'b0;
                end else begin
                    cnt_p <= cnt_p + ratio_one;
                end
            end
        end
    end

    // -------------------------------------------------------------------------
    // Negative-edge phase for odd-ratio balancing.  restart_n is launched on
    // posedge clk and is held long enough to clear this half-cycle phase.
    // -------------------------------------------------------------------------
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt_n <= RATIO_ZERO;
            clk_n <= 1'b0;
        end else if (restart_n || !ratio_active) begin
            cnt_n <= RATIO_ZERO;
            clk_n <= 1'b0;
        end else if (!ratio_odd) begin
            cnt_n <= RATIO_ZERO;
            clk_n <= 1'b0;
        end else if (!clk_n) begin
            if (cnt_n == (odd_low_limit - ratio_one)) begin
                cnt_n <= RATIO_ZERO;
                clk_n <= 1'b1;
            end else begin
                cnt_n <= cnt_n + ratio_one;
            end
        end else begin
            if (cnt_n == (odd_high_limit - ratio_one)) begin
                cnt_n <= RATIO_ZERO;
                clk_n <= 1'b0;
            end else begin
                cnt_n <= cnt_n + ratio_one;
            end
        end
    end

    // -------------------------------------------------------------------------
    // Output mode selection:
    //   0    : force low
    //   1    : combinational clock bypass
    //   even : positive-edge divided phase
    //   odd  : OR-combined positive/negative phases for half-cycle balance
    // -------------------------------------------------------------------------
    always @(*) begin
        if (ratio_zero) begin
            clk_out = 1'b0;
        end else if (ratio_is_one) begin
            clk_out = clk;
        end else if (restart_n) begin
            clk_out = 1'b0;
        end else if (ratio_odd) begin
            clk_out = clk_p | clk_n;
        end else begin
            clk_out = clk_p;
        end
    end

endmodule
