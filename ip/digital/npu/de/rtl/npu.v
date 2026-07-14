//============================================================================
// Module     : npu
// Function   : Tiny software-managed signed INT8 inference-layer accelerator
//============================================================================

module npu #(
    parameter integer ACT_SPM_BYTES  = 64,
    parameter integer WGT_SPM_BYTES  = 64,
    parameter integer OUT_SPM_BYTES  = 64,
    parameter integer BIAS_SPM_WORDS = 16
) (
    input         clk,
    input         rst_n,
    input         mm_valid,
    input         mm_write,
    input  [15:0] mm_addr,
    input  [31:0] mm_wdata,
    input  [3:0]  mm_wstrb,
    output reg [31:0] mm_rdata,
    output        mm_ready,
    output reg    mm_error,
    output        irq
);

    localparam ACT_BASE_ADDR      = 16'h0100;
    localparam WGT_BASE_ADDR      = 16'h0200;
    localparam OUT_BASE_ADDR      = 16'h0300;
    localparam BIAS_BASE_ADDR     = 16'h0400;
    localparam ERR_INVALID_ADDR   = 5'd5;

    wire busy;
    wire reg_region;
    wire act_window;
    wire wgt_window;
    wire out_window;
    wire bias_window;
    wire byte_spm_window;
    wire spm_window;
    wire spm_stall;
    wire accepted;
    wire aligned;
    wire [5:0] byte_spm_offset;
    wire [3:0] bias_spm_index;

    wire [31:0] regs_rdata;
    wire        regs_error;
    wire [4:0]  regs_error_code;
    wire [31:0] spm_rdata;
    wire        spm_error;
    wire [4:0]  spm_error_code;

    reg [31:0] host_rdata;
    reg        host_error;
    reg [4:0]  host_error_code;

    wire soft_reset_pulse;
    wire start_pulse;

    wire [7:0]  cfg_k_count_m1;
    wire [7:0]  cfg_act_stride_m1;
    wire [7:0]  act_base_reg;
    wire [7:0]  wgt_base_reg;
    wire [7:0]  out_base_reg;
    wire [31:0] acc_init_reg;
    wire [7:0]  out_count_m1_reg;
    wire [7:0]  out_stride_m1_reg;
    wire [7:0]  wgt_stride_m1_reg;
    wire [3:0]  bias_base_reg;
    wire [31:0] quant_mult_reg;
    wire [5:0]  quant_shift_reg;
    wire [7:0]  out_zero_point_reg;
    wire [1:0]  activation_mode_reg;
    wire [7:0]  relu6_max_reg;

    wire        core_status_done_set;
    wire        core_status_error_set;
    wire [4:0]  core_status_error_code;
    wire        core_status_sat_overflow_set;
    wire [31:0] core_acc_result;
    wire [7:0]  core_last_out_count;

    wire [5:0]  core_act_rd_addr;
    wire [5:0]  core_wgt_rd_addr;
    wire [3:0]  core_bias_rd_addr;
    wire [5:0]  core_out_wr_addr;
    wire [7:0]  core_out_wr_data;
    wire        core_out_wr_en;
    wire [31:0] spm_act_word;
    wire [31:0] spm_wgt_word;
    wire [31:0] spm_bias_word;

    generate
        if ((ACT_SPM_BYTES < 4) || (ACT_SPM_BYTES > 64) ||
            ((ACT_SPM_BYTES % 4) != 0) ||
            (WGT_SPM_BYTES < 4) || (WGT_SPM_BYTES > 64) ||
            ((WGT_SPM_BYTES % 4) != 0) ||
            (OUT_SPM_BYTES < 4) || (OUT_SPM_BYTES > 64) ||
            ((OUT_SPM_BYTES % 4) != 0) ||
            (BIAS_SPM_WORDS < 1) || (BIAS_SPM_WORDS > 16)) begin : g_invalid_parameters
            initial begin
                $display("ERROR: illegal npu scratchpad capacity parameter");
                $finish;
            end
        end
    endgenerate

    assign reg_region      = (mm_addr < 16'h0100);
    assign act_window      = (mm_addr >= ACT_BASE_ADDR) &&
                             (mm_addr <= 16'h013f);
    assign wgt_window      = (mm_addr >= WGT_BASE_ADDR) &&
                             (mm_addr <= 16'h023f);
    assign out_window      = (mm_addr >= OUT_BASE_ADDR) &&
                             (mm_addr <= 16'h033f);
    assign bias_window     = (mm_addr >= BIAS_BASE_ADDR) &&
                             (mm_addr <= 16'h043f);
    assign byte_spm_window = act_window || wgt_window || out_window;
    assign spm_window      = byte_spm_window || bias_window;
    assign spm_stall       = mm_valid && spm_window && busy;
    assign mm_ready        = !spm_stall;
    assign accepted        = mm_valid && mm_ready;
    assign aligned         = (mm_addr[1:0] == 2'b00);
    assign byte_spm_offset = mm_addr[5:0];
    assign bias_spm_index  = mm_addr[5:2];

    always @* begin
        host_rdata      = 32'h0000_0000;
        host_error      = 1'b0;
        host_error_code = 5'd0;

        if (accepted) begin
            if (reg_region) begin
                host_rdata      = regs_rdata;
                host_error      = regs_error;
                host_error_code = regs_error_code;
            end else if (spm_window) begin
                host_rdata      = spm_rdata;
                host_error      = spm_error;
                host_error_code = spm_error_code;
            end else begin
                host_error      = 1'b1;
                host_error_code = ERR_INVALID_ADDR;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mm_rdata <= 32'h0000_0000;
            mm_error <= 1'b0;
        end else if (soft_reset_pulse) begin
            mm_rdata <= 32'h0000_0000;
            mm_error <= 1'b0;
        end else begin
            if (accepted) begin
                mm_rdata <= host_rdata;
                mm_error <= host_error;
            end else if (!spm_stall) begin
                mm_rdata <= 32'h0000_0000;
                mm_error <= 1'b0;
            end
        end
    end

    npu_regs u_npu_regs (
        .clk                         (clk),
        .rst_n                       (rst_n),
        .accepted_i                  (accepted),
        .reg_access_i                (accepted && reg_region),
        .mm_write_i                  (mm_write),
        .mm_addr_i                   (mm_addr),
        .mm_wdata_i                  (mm_wdata),
        .mm_wstrb_i                  (mm_wstrb),
        .aligned_i                   (aligned),
        .host_error_i                (host_error),
        .host_error_code_i           (host_error_code),
        .busy_i                      (busy),
        .core_status_done_set_i      (core_status_done_set),
        .core_status_error_set_i     (core_status_error_set),
        .core_status_error_code_i    (core_status_error_code),
        .core_status_sat_overflow_i  (core_status_sat_overflow_set),
        .acc_result_i                (core_acc_result),
        .last_out_count_i            (core_last_out_count),
        .host_rdata_o                (regs_rdata),
        .host_error_o                (regs_error),
        .host_error_code_o           (regs_error_code),
        .soft_reset_pulse_o          (soft_reset_pulse),
        .start_pulse_o               (start_pulse),
        .irq_o                       (irq),
        .cfg_k_count_m1_o            (cfg_k_count_m1),
        .cfg_act_stride_m1_o         (cfg_act_stride_m1),
        .act_base_o                  (act_base_reg),
        .wgt_base_o                  (wgt_base_reg),
        .out_base_o                  (out_base_reg),
        .acc_init_o                  (acc_init_reg),
        .out_count_m1_o              (out_count_m1_reg),
        .out_stride_m1_o             (out_stride_m1_reg),
        .wgt_stride_m1_o             (wgt_stride_m1_reg),
        .bias_base_o                 (bias_base_reg),
        .quant_mult_o                (quant_mult_reg),
        .quant_shift_o               (quant_shift_reg),
        .out_zero_point_o            (out_zero_point_reg),
        .activation_mode_o           (activation_mode_reg),
        .relu6_max_o                 (relu6_max_reg)
    );

    npu_spm #(
        .ACT_SPM_BYTES              (ACT_SPM_BYTES),
        .WGT_SPM_BYTES              (WGT_SPM_BYTES),
        .OUT_SPM_BYTES              (OUT_SPM_BYTES),
        .BIAS_SPM_WORDS             (BIAS_SPM_WORDS)
    ) u_npu_spm (
        .clk                         (clk),
        .rst_n                       (rst_n),
        .soft_reset_i                (soft_reset_pulse),
        .access_i                    (accepted && spm_window),
        .mm_write_i                  (mm_write),
        .mm_wdata_i                  (mm_wdata),
        .mm_wstrb_i                  (mm_wstrb),
        .aligned_i                   (aligned),
        .act_window_i                (act_window),
        .wgt_window_i                (wgt_window),
        .out_window_i                (out_window),
        .bias_window_i               (bias_window),
        .byte_offset_i               (byte_spm_offset),
        .bias_index_i                (bias_spm_index),
        .host_error_i                (host_error),
        .host_rdata_o                (spm_rdata),
        .host_error_o                (spm_error),
        .host_error_code_o           (spm_error_code),
        .act_rd_addr_i               (core_act_rd_addr),
        .wgt_rd_addr_i               (core_wgt_rd_addr),
        .bias_rd_addr_i              (core_bias_rd_addr),
        .act_word_o                  (spm_act_word),
        .wgt_word_o                  (spm_wgt_word),
        .bias_word_o                 (spm_bias_word),
        .out_wr_en_i                 (core_out_wr_en),
        .out_wr_addr_i               (core_out_wr_addr),
        .out_wr_data_i               (core_out_wr_data)
    );

    npu_core #(
        .ACT_SPM_BYTES              (ACT_SPM_BYTES),
        .WGT_SPM_BYTES              (WGT_SPM_BYTES),
        .OUT_SPM_BYTES              (OUT_SPM_BYTES),
        .BIAS_SPM_WORDS             (BIAS_SPM_WORDS)
    ) u_npu_core (
        .clk                         (clk),
        .rst_n                       (rst_n),
        .soft_reset_i                (soft_reset_pulse),
        .start_pulse_i               (start_pulse),
        .cfg_k_count_m1_i            (cfg_k_count_m1),
        .cfg_act_stride_m1_i         (cfg_act_stride_m1),
        .act_base_i                  (act_base_reg),
        .wgt_base_i                  (wgt_base_reg),
        .out_base_i                  (out_base_reg),
        .acc_init_i                  (acc_init_reg),
        .out_count_m1_i              (out_count_m1_reg),
        .out_stride_m1_i             (out_stride_m1_reg),
        .wgt_stride_m1_i             (wgt_stride_m1_reg),
        .bias_base_i                 (bias_base_reg),
        .quant_mult_i                (quant_mult_reg),
        .quant_shift_i               (quant_shift_reg),
        .out_zero_point_i            (out_zero_point_reg),
        .activation_mode_i           (activation_mode_reg),
        .relu6_max_i                 (relu6_max_reg),
        .act_word_i                  (spm_act_word),
        .wgt_word_i                  (spm_wgt_word),
        .bias_word_i                 (spm_bias_word),
        .busy_o                      (busy),
        .act_rd_addr_o               (core_act_rd_addr),
        .wgt_rd_addr_o               (core_wgt_rd_addr),
        .bias_rd_addr_o              (core_bias_rd_addr),
        .out_wr_en_o                 (core_out_wr_en),
        .out_wr_addr_o               (core_out_wr_addr),
        .out_wr_data_o               (core_out_wr_data),
        .status_done_set_o           (core_status_done_set),
        .status_error_set_o          (core_status_error_set),
        .status_error_code_o         (core_status_error_code),
        .status_sat_overflow_set_o   (core_status_sat_overflow_set),
        .acc_result_o                (core_acc_result),
        .last_out_count_o            (core_last_out_count)
    );

endmodule
