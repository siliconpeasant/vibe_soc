//============================================================================
// Module     : npu_core
// Function   : Descriptor checks, command FSM, counters, MAC/requant sequencing
//============================================================================

module npu_core #(
    parameter integer ACT_SPM_BYTES  = 64,
    parameter integer WGT_SPM_BYTES  = 64,
    parameter integer OUT_SPM_BYTES  = 64,
    parameter integer BIAS_SPM_WORDS = 16
) (
    input         clk,
    input         rst_n,
    input         soft_reset_i,
    input         start_pulse_i,
    input  [7:0]  cfg_k_count_m1_i,
    input  [7:0]  cfg_act_stride_m1_i,
    input  [7:0]  act_base_i,
    input  [7:0]  wgt_base_i,
    input  [7:0]  out_base_i,
    input  [31:0] acc_init_i,
    input  [7:0]  out_count_m1_i,
    input  [7:0]  out_stride_m1_i,
    input  [7:0]  wgt_stride_m1_i,
    input  [3:0]  bias_base_i,
    input  [31:0] quant_mult_i,
    input  [5:0]  quant_shift_i,
    input  [7:0]  out_zero_point_i,
    input  [1:0]  activation_mode_i,
    input  [7:0]  relu6_max_i,
    input  [31:0] act_word_i,
    input  [31:0] wgt_word_i,
    input  [31:0] bias_word_i,
    output        busy_o,
    output [5:0]  act_rd_addr_o,
    output [5:0]  wgt_rd_addr_o,
    output [3:0]  bias_rd_addr_o,
    output        out_wr_en_o,
    output [5:0]  out_wr_addr_o,
    output [7:0]  out_wr_data_o,
    output        status_done_set_o,
    output        status_error_set_o,
    output reg [4:0] status_error_code_o,
    output        status_sat_overflow_set_o,
    output [31:0] acc_result_o,
    output [7:0]  last_out_count_o
);

    localparam ERR_NONE            = 5'd0;
    localparam ERR_DESC_ACT_RANGE  = 5'd2;
    localparam ERR_DESC_WGT_RANGE  = 5'd3;
    localparam ERR_DESC_OUT_RANGE  = 5'd4;
    localparam ERR_DESC_BIAS_RANGE = 5'd9;
    localparam ERR_DESC_Q_SHIFT    = 5'd10;
    localparam ERR_DESC_ACTIVATION = 5'd11;

    localparam ACT_NONE            = 2'd0;
    localparam ACT_RELU6           = 2'd2;

    localparam [17:0] ACT_SPM_BYTES_VALUE  = ACT_SPM_BYTES[17:0];
    localparam [17:0] WGT_SPM_BYTES_VALUE  = WGT_SPM_BYTES[17:0];
    localparam [17:0] OUT_SPM_BYTES_VALUE  = OUT_SPM_BYTES[17:0];
    localparam [8:0]  BIAS_SPM_WORDS_VALUE = BIAS_SPM_WORDS[8:0];

    localparam ST_IDLE             = 4'd0;
    localparam ST_CHECK            = 4'd1;
    localparam ST_LOAD             = 4'd2;
    localparam ST_MAC              = 4'd3;
    localparam ST_BIAS             = 4'd4;
    localparam ST_REQUANT          = 4'd5;
    localparam ST_STORE            = 4'd6;

    reg [3:0]  state;
    reg [7:0]  desc_k_count_m1;
    reg [8:0]  desc_act_stride;
    reg [7:0]  desc_act_base;
    reg [7:0]  desc_wgt_base;
    reg [7:0]  desc_out_base;
    reg [7:0]  desc_out_count_m1;
    reg [8:0]  desc_out_stride;
    reg [8:0]  desc_wgt_stride;
    reg [3:0]  desc_bias_base;
    reg [31:0] desc_acc_init;
    reg [31:0] desc_quant_mult;
    reg [5:0]  desc_quant_shift;
    reg [7:0]  desc_out_zero_point;
    reg [1:0]  desc_activation_mode;
    reg [7:0]  desc_relu6_max;
    reg [7:0]  out_idx;
    reg [7:0]  k_idx;
    // Descriptor checks guarantee that every active running address fits 6 bits.
    reg [5:0]  act_rd_addr_reg;
    reg [5:0]  wgt_row_base_reg;
    reg [5:0]  wgt_rd_addr_reg;
    reg [5:0]  out_wr_addr_reg;
    reg [31:0] acc_work;
    reg [31:0] post_bias_reg;
    reg [7:0]  requant_byte_reg;
    reg        requant_clip_reg;
    reg [31:0] acc_result_reg;
    reg [7:0]  last_out_count_reg;

    reg signed [7:0] act_lane0;
    reg signed [7:0] act_lane1;
    reg signed [7:0] act_lane2;
    reg signed [7:0] act_lane3;
    reg signed [7:0] wgt_lane0;
    reg signed [7:0] wgt_lane1;
    reg signed [7:0] wgt_lane2;
    reg signed [7:0] wgt_lane3;

    wire [17:0] desc_act_last;
    wire [17:0] desc_wgt_last;
    wire [17:0] desc_out_last;
    wire [8:0]  desc_bias_last;
    wire signed [7:0] desc_out_zp_signed;
    wire signed [7:0] desc_relu6_signed;
    wire desc_activation_bad;
    wire desc_error;
    wire compute_addr_valid;
    wire [3:0] bias_rd_addr_calc;
    wire signed [31:0] mac_acc_next;
    wire [7:0] requant_byte;
    wire       requant_clip;

    generate
        if ((ACT_SPM_BYTES < 4) || (ACT_SPM_BYTES > 64) ||
            ((ACT_SPM_BYTES % 4) != 0) ||
            (WGT_SPM_BYTES < 4) || (WGT_SPM_BYTES > 64) ||
            ((WGT_SPM_BYTES % 4) != 0) ||
            (OUT_SPM_BYTES < 4) || (OUT_SPM_BYTES > 64) ||
            ((OUT_SPM_BYTES % 4) != 0) ||
            (BIAS_SPM_WORDS < 1) || (BIAS_SPM_WORDS > 16)) begin : g_invalid_parameters
            initial begin
                $display("ERROR: illegal npu_core capacity parameter");
                $finish;
            end
        end
    endgenerate

    assign busy_o = (state != ST_IDLE);

    assign desc_act_last = {10'd0, desc_act_base} +
                           ({10'd0, desc_k_count_m1} *
                            {9'd0, desc_act_stride}) +
                           18'd3;
    assign desc_wgt_last = {10'd0, desc_wgt_base} +
                           ({10'd0, desc_out_count_m1} *
                            {9'd0, desc_wgt_stride}) +
                           ({10'd0, desc_k_count_m1} * 18'd4) +
                           18'd3;
    assign desc_out_last = {10'd0, desc_out_base} +
                           ({10'd0, desc_out_count_m1} *
                            {9'd0, desc_out_stride});
    assign desc_bias_last = {5'd0, desc_bias_base} +
                            {1'b0, desc_out_count_m1};
    assign desc_out_zp_signed = desc_out_zero_point;
    assign desc_relu6_signed  = desc_relu6_max;
    assign desc_activation_bad =
        (desc_activation_mode > ACT_RELU6) ||
        ((desc_activation_mode == ACT_RELU6) &&
         (desc_relu6_signed < desc_out_zp_signed));

    assign desc_error = (status_error_code_o != ERR_NONE);

    assign bias_rd_addr_calc = desc_bias_base + out_idx[3:0];

    // Keep behavioral scratchpad indices in range until ST_CHECK has accepted
    // the complete descriptor. This internal signal is intentionally visible
    // by hierarchy so DV can check that speculative reads remain clamped.
    assign compute_addr_valid = (state != ST_IDLE) &&
                                (state != ST_CHECK) &&
                                !desc_error;
    assign act_rd_addr_o  = compute_addr_valid ? act_rd_addr_reg : 6'd0;
    assign wgt_rd_addr_o  = compute_addr_valid ? wgt_rd_addr_reg : 6'd0;
    assign bias_rd_addr_o = compute_addr_valid ? bias_rd_addr_calc : 4'd0;
    assign out_wr_addr_o  = compute_addr_valid ? out_wr_addr_reg : 6'd0;
    assign out_wr_en_o    = (state == ST_STORE);
    assign out_wr_data_o  = requant_byte_reg;

    assign status_error_set_o =
        (state == ST_CHECK) && desc_error;
    assign status_done_set_o =
        (state == ST_STORE) && (out_idx == desc_out_count_m1);
    assign status_sat_overflow_set_o =
        (state == ST_STORE) && requant_clip_reg;

    assign acc_result_o      = acc_result_reg;
    assign last_out_count_o  = last_out_count_reg;

    always @* begin
        status_error_code_o = ERR_NONE;
        if (desc_act_last >= ACT_SPM_BYTES_VALUE) begin
            status_error_code_o = ERR_DESC_ACT_RANGE;
        end else if (desc_wgt_last >= WGT_SPM_BYTES_VALUE) begin
            status_error_code_o = ERR_DESC_WGT_RANGE;
        end else if (desc_out_last >= OUT_SPM_BYTES_VALUE) begin
            status_error_code_o = ERR_DESC_OUT_RANGE;
        end else if (desc_bias_last >= BIAS_SPM_WORDS_VALUE) begin
            status_error_code_o = ERR_DESC_BIAS_RANGE;
        end else if (desc_quant_shift > 6'd31) begin
            status_error_code_o = ERR_DESC_Q_SHIFT;
        end else if (desc_activation_bad) begin
            status_error_code_o = ERR_DESC_ACTIVATION;
        end
    end

    npu_mac u_npu_mac (
        .acc_i  ($signed(acc_work)),
        .act0_i (act_lane0),
        .act1_i (act_lane1),
        .act2_i (act_lane2),
        .act3_i (act_lane3),
        .wgt0_i (wgt_lane0),
        .wgt1_i (wgt_lane1),
        .wgt2_i (wgt_lane2),
        .wgt3_i (wgt_lane3),
        .acc_o  (mac_acc_next)
    );

    npu_requant u_npu_requant (
        .post_bias_i       ($signed(post_bias_reg)),
        .quant_mult_i      ($signed(desc_quant_mult)),
        .quant_shift_i     (desc_quant_shift),
        .out_zero_point_i  (desc_out_zero_point),
        .activation_mode_i (desc_activation_mode),
        .relu6_max_i       (desc_relu6_max),
        .out_byte_o        (requant_byte),
        .sat_clip_o        (requant_clip)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state                <= ST_IDLE;
            desc_k_count_m1      <= 8'h00;
            desc_act_stride      <= 9'd4;
            desc_act_base        <= 8'h00;
            desc_wgt_base        <= 8'h00;
            desc_out_base        <= 8'h00;
            desc_out_count_m1    <= 8'h00;
            desc_out_stride      <= 9'd1;
            desc_wgt_stride      <= 9'd4;
            desc_bias_base       <= 4'h0;
            desc_acc_init        <= 32'h0000_0000;
            desc_quant_mult      <= 32'h0000_0001;
            desc_quant_shift     <= 6'h00;
            desc_out_zero_point  <= 8'h00;
            desc_activation_mode <= ACT_NONE;
            desc_relu6_max       <= 8'h7f;
            out_idx              <= 8'h00;
            k_idx                <= 8'h00;
            act_rd_addr_reg      <= 6'h00;
            wgt_row_base_reg     <= 6'h00;
            wgt_rd_addr_reg      <= 6'h00;
            out_wr_addr_reg      <= 6'h00;
            acc_work             <= 32'h0000_0000;
            post_bias_reg        <= 32'h0000_0000;
            requant_byte_reg     <= 8'h00;
            requant_clip_reg     <= 1'b0;
            acc_result_reg       <= 32'h0000_0000;
            last_out_count_reg   <= 8'h00;
            act_lane0            <= 8'sd0;
            act_lane1            <= 8'sd0;
            act_lane2            <= 8'sd0;
            act_lane3            <= 8'sd0;
            wgt_lane0            <= 8'sd0;
            wgt_lane1            <= 8'sd0;
            wgt_lane2            <= 8'sd0;
            wgt_lane3            <= 8'sd0;
        end else if (soft_reset_i) begin
            state                <= ST_IDLE;
            desc_k_count_m1      <= 8'h00;
            desc_act_stride      <= 9'd4;
            desc_act_base        <= 8'h00;
            desc_wgt_base        <= 8'h00;
            desc_out_base        <= 8'h00;
            desc_out_count_m1    <= 8'h00;
            desc_out_stride      <= 9'd1;
            desc_wgt_stride      <= 9'd4;
            desc_bias_base       <= 4'h0;
            desc_acc_init        <= 32'h0000_0000;
            desc_quant_mult      <= 32'h0000_0001;
            desc_quant_shift     <= 6'h00;
            desc_out_zero_point  <= 8'h00;
            desc_activation_mode <= ACT_NONE;
            desc_relu6_max       <= 8'h7f;
            out_idx              <= 8'h00;
            k_idx                <= 8'h00;
            act_rd_addr_reg      <= 6'h00;
            wgt_row_base_reg     <= 6'h00;
            wgt_rd_addr_reg      <= 6'h00;
            out_wr_addr_reg      <= 6'h00;
            acc_work             <= 32'h0000_0000;
            post_bias_reg        <= 32'h0000_0000;
            requant_byte_reg     <= 8'h00;
            requant_clip_reg     <= 1'b0;
            acc_result_reg       <= 32'h0000_0000;
            last_out_count_reg   <= 8'h00;
            act_lane0            <= 8'sd0;
            act_lane1            <= 8'sd0;
            act_lane2            <= 8'sd0;
            act_lane3            <= 8'sd0;
            wgt_lane0            <= 8'sd0;
            wgt_lane1            <= 8'sd0;
            wgt_lane2            <= 8'sd0;
            wgt_lane3            <= 8'sd0;
        end else begin
            if (start_pulse_i && busy_o) begin
                state <= ST_IDLE;
            end else if (start_pulse_i) begin
                state                <= ST_CHECK;
                desc_k_count_m1      <= cfg_k_count_m1_i;
                desc_act_stride      <= {1'b0, cfg_act_stride_m1_i} + 9'd1;
                desc_act_base        <= act_base_i;
                desc_wgt_base        <= wgt_base_i;
                desc_out_base        <= out_base_i;
                desc_out_count_m1    <= out_count_m1_i;
                desc_out_stride      <= {1'b0, out_stride_m1_i} + 9'd1;
                desc_wgt_stride      <= {1'b0, wgt_stride_m1_i} + 9'd1;
                desc_bias_base       <= bias_base_i;
                desc_acc_init        <= acc_init_i;
                desc_quant_mult      <= quant_mult_i;
                desc_quant_shift     <= quant_shift_i;
                desc_out_zero_point  <= out_zero_point_i;
                desc_activation_mode <= activation_mode_i;
                desc_relu6_max       <= relu6_max_i;
                out_idx              <= 8'h00;
                k_idx                <= 8'h00;
                act_rd_addr_reg      <= act_base_i[5:0];
                wgt_row_base_reg     <= wgt_base_i[5:0];
                wgt_rd_addr_reg      <= wgt_base_i[5:0];
                out_wr_addr_reg      <= out_base_i[5:0];
                acc_work             <= acc_init_i;
                post_bias_reg        <= 32'h0000_0000;
                requant_byte_reg     <= 8'h00;
                requant_clip_reg     <= 1'b0;
                last_out_count_reg   <= 8'h00;
            end else begin
                case (state)
                    ST_IDLE: begin
                        state <= ST_IDLE;
                    end
                    ST_CHECK: begin
                        if (desc_error) begin
                            state <= ST_IDLE;
                        end else begin
                            state <= ST_LOAD;
                        end
                    end
                    ST_LOAD: begin
                        act_lane0 <= act_word_i[7:0];
                        act_lane1 <= act_word_i[15:8];
                        act_lane2 <= act_word_i[23:16];
                        act_lane3 <= act_word_i[31:24];
                        wgt_lane0 <= wgt_word_i[7:0];
                        wgt_lane1 <= wgt_word_i[15:8];
                        wgt_lane2 <= wgt_word_i[23:16];
                        wgt_lane3 <= wgt_word_i[31:24];
                        state     <= ST_MAC;
                    end
                    ST_MAC: begin
                        acc_work <= mac_acc_next;
                        if (k_idx == desc_k_count_m1) begin
                            state <= ST_BIAS;
                        end else begin
                            k_idx           <= k_idx + 8'd1;
                            act_rd_addr_reg <= act_rd_addr_reg +
                                               desc_act_stride[5:0];
                            wgt_rd_addr_reg <= wgt_rd_addr_reg + 6'd4;
                            state           <= ST_LOAD;
                        end
                    end
                    ST_BIAS: begin
                        post_bias_reg <=
                            $signed(acc_work) +
                            $signed(bias_word_i);
                        state <= ST_REQUANT;
                    end
                    ST_REQUANT: begin
                        requant_byte_reg <= requant_byte;
                        requant_clip_reg <= requant_clip;
                        state            <= ST_STORE;
                    end
                    ST_STORE: begin
                        acc_result_reg     <= post_bias_reg;
                        last_out_count_reg <= last_out_count_reg + 8'd1;
                        if (out_idx == desc_out_count_m1) begin
                            state <= ST_IDLE;
                        end else begin
                            out_idx          <= out_idx + 8'd1;
                            k_idx            <= 8'h00;
                            act_rd_addr_reg  <= desc_act_base[5:0];
                            wgt_row_base_reg <= wgt_row_base_reg +
                                                desc_wgt_stride[5:0];
                            wgt_rd_addr_reg  <= wgt_row_base_reg +
                                                desc_wgt_stride[5:0];
                            out_wr_addr_reg  <= out_wr_addr_reg +
                                                desc_out_stride[5:0];
                            acc_work        <= desc_acc_init;
                            state           <= ST_LOAD;
                        end
                    end
                    default: begin
                        state <= ST_IDLE;
                    end
                endcase
            end
        end
    end

endmodule
