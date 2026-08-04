// Module   : clk_divider_wrap
// Function : Programmable clock divider wrapper used by crg-gen.
//            Provides cfg-domain handshakes around a synthesizable divider core.

module clk_divider_wrap #(
    parameter PRRWIDTH      = 3,
    parameter BYPASS        = 1'b0,
    parameter DELAY_2       = 1'b1,
    parameter DIV_VAL_TO_EN = 1'b0,
    parameter DEFAULT_VALUE = 2
) (
    input  wire                      test_mode,
    input  wire                      cfg_clk,
    input  wire                      cfg_rst_n,
    input  wire                      clk_div_sync_clk,
    input  wire                      clk_in,
    input  wire                      clk_gen_rst_n,
    input  wire                      clk_div_to_en,
    input  wire [PRRWIDTH-1:0]       clk_to_divider,
    input  wire                      clk_divider_ea_req,
    output reg  [PRRWIDTH-1:0]       clk_divider,
    output reg  [PRRWIDTH-1:0]       clk_divider_status,
    output reg                       clk_divider_done,
    output wire                      clk_dived
);

    localparam [PRRWIDTH-1:0] DEF_DIV = DEFAULT_VALUE[PRRWIDTH-1:0];

    reg [PRRWIDTH-1:0] div_live;
    reg [PRRWIDTH-1:0] div_applied;
    reg                req_d;

    // Capture software divider on cfg clock when enable request rises.
    always @(posedge cfg_clk or negedge cfg_rst_n) begin
        if (!cfg_rst_n) begin
            div_live          <= DEF_DIV;
            clk_divider       <= DEF_DIV;
            clk_divider_status<= DEF_DIV;
            clk_divider_done  <= 1'b0;
            req_d             <= 1'b0;
        end else begin
            req_d <= clk_divider_ea_req;
            clk_divider_done <= 1'b0;
            if (clk_divider_ea_req && !req_d) begin
                div_live           <= (clk_to_divider == {PRRWIDTH{1'b0}}) ? DEF_DIV : clk_to_divider;
                clk_divider        <= (clk_to_divider == {PRRWIDTH{1'b0}}) ? DEF_DIV : clk_to_divider;
                clk_divider_status <= (clk_to_divider == {PRRWIDTH{1'b0}}) ? DEF_DIV : clk_to_divider;
                clk_divider_done   <= 1'b1;
            end else begin
                clk_divider_status <= div_applied;
            end
        end
    end

    // Resample applied ratio into divider clock domain.
    always @(posedge clk_div_sync_clk or negedge clk_gen_rst_n) begin
        if (!clk_gen_rst_n)
            div_applied <= DEF_DIV;
        else if (clk_div_to_en || DIV_VAL_TO_EN)
            div_applied <= div_live;
        else
            div_applied <= div_live;
    end

    // Simple integer divider (toggle) for functional CRG connectivity.
    // BYPASS forces pass-through; test_mode may also bypass.
    reg                      clk_div_r;
    reg [PRRWIDTH:0]         cnt;

    wire bypass_now = BYPASS || test_mode || (div_applied <= {{(PRRWIDTH-1){1'b0}}, 1'b1});

    always @(posedge clk_in or negedge clk_gen_rst_n) begin
        if (!clk_gen_rst_n) begin
            cnt       <= {(PRRWIDTH+1){1'b0}};
            clk_div_r <= 1'b0;
        end else if (bypass_now) begin
            cnt       <= {(PRRWIDTH+1){1'b0}};
            clk_div_r <= 1'b0;
        end else if (cnt >= ({1'b0, div_applied} - 1'b1)) begin
            cnt       <= {(PRRWIDTH+1){1'b0}};
            clk_div_r <= ~clk_div_r;
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign clk_dived = bypass_now ? clk_in : clk_div_r;

endmodule
