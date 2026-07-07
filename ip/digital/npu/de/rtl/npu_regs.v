//============================================================================
// Module     : npu_regs
// Function   : NPU architectural registers, status, and register MMIO decode
//============================================================================

module npu_regs (
    input         clk,
    input         rst_n,
    input         accepted_i,
    input         reg_access_i,
    input         mm_write_i,
    input  [15:0] mm_addr_i,
    input  [31:0] mm_wdata_i,
    input  [3:0]  mm_wstrb_i,
    input         aligned_i,
    input         host_error_i,
    input  [4:0]  host_error_code_i,
    input         busy_i,
    input         core_status_done_set_i,
    input         core_status_error_set_i,
    input  [4:0]  core_status_error_code_i,
    input         core_status_sat_overflow_i,
    input  [31:0] acc_result_i,
    input  [7:0]  last_out_count_i,
    output reg [31:0] host_rdata_o,
    output reg        host_error_o,
    output reg [4:0]  host_error_code_o,
    output            soft_reset_pulse_o,
    output            start_pulse_o,
    output            irq_o,
    output [7:0]      cfg_k_count_m1_o,
    output [7:0]      cfg_act_stride_m1_o,
    output [7:0]      act_base_o,
    output [7:0]      wgt_base_o,
    output [7:0]      out_base_o,
    output [31:0]     acc_init_o,
    output [7:0]      out_count_m1_o,
    output [7:0]      out_stride_m1_o,
    output [7:0]      wgt_stride_m1_o,
    output [3:0]      bias_base_o,
    output [31:0]     quant_mult_o,
    output [5:0]      quant_shift_o,
    output [7:0]      out_zero_point_o,
    output [1:0]      activation_mode_o,
    output [7:0]      relu6_max_o
);

    localparam ADDR_CTRL           = 16'h0000;
    localparam ADDR_STATUS         = 16'h0004;
    localparam ADDR_CFG            = 16'h0008;
    localparam ADDR_ACT_BASE       = 16'h000c;
    localparam ADDR_WGT_BASE       = 16'h0010;
    localparam ADDR_OUT_BASE       = 16'h0014;
    localparam ADDR_ACC_INIT       = 16'h0018;
    localparam ADDR_ACC_RESULT     = 16'h001c;
    localparam ADDR_ERR_CODE       = 16'h0020;
    localparam ADDR_OUT_CFG        = 16'h0024;
    localparam ADDR_BIAS_BASE      = 16'h0028;
    localparam ADDR_QUANT_MULT     = 16'h002c;
    localparam ADDR_QUANT_CFG      = 16'h0030;
    localparam ADDR_LAST_OUT_COUNT = 16'h0034;

    localparam ERR_NONE            = 5'd0;
    localparam ERR_START_BUSY      = 5'd1;
    localparam ERR_INVALID_ADDR    = 5'd5;
    localparam ERR_REG_UNALIGNED   = 5'd6;
    localparam ERR_BAD_REG_WSTRB   = 5'd7;
    localparam ERR_RO_WRITE        = 5'd12;

    localparam ACT_NONE            = 2'd0;

    reg        irq_en;
    reg        status_done;
    reg        status_error;
    reg        status_sat_overflow;
    reg [7:0]  cfg_k_count_m1;
    reg [7:0]  cfg_act_stride_m1;
    reg [7:0]  act_base_reg;
    reg [7:0]  wgt_base_reg;
    reg [7:0]  out_base_reg;
    reg [31:0] acc_init_reg;
    reg [4:0]  err_code_reg;
    reg [7:0]  out_count_m1_reg;
    reg [7:0]  out_stride_m1_reg;
    reg [7:0]  wgt_stride_m1_reg;
    reg [3:0]  bias_base_reg;
    reg [31:0] quant_mult_reg;
    reg [5:0]  quant_shift_reg;
    reg [7:0]  out_zero_point_reg;
    reg [1:0]  activation_mode_reg;
    reg [7:0]  relu6_max_reg;

    wire ctrl_write;
    wire status_write;
    wire cfg_write;
    wire act_base_write;
    wire wgt_base_write;
    wire out_base_write;
    wire acc_init_write;
    wire err_code_write;
    wire out_cfg_write;
    wire bias_base_write;
    wire quant_mult_write;
    wire quant_cfg_write;

    assign ctrl_write       = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_CTRL);
    assign status_write     = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_STATUS);
    assign cfg_write        = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_CFG);
    assign act_base_write   = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_ACT_BASE);
    assign wgt_base_write   = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_WGT_BASE);
    assign out_base_write   = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_OUT_BASE);
    assign acc_init_write   = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_ACC_INIT);
    assign err_code_write   = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_ERR_CODE);
    assign out_cfg_write    = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_OUT_CFG);
    assign bias_base_write  = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_BIAS_BASE);
    assign quant_mult_write = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_QUANT_MULT);
    assign quant_cfg_write  = accepted_i && mm_write_i && !host_error_i &&
                              (mm_addr_i == ADDR_QUANT_CFG);

    assign soft_reset_pulse_o = ctrl_write && mm_wdata_i[1];
    assign start_pulse_o      = ctrl_write && mm_wdata_i[0] && !mm_wdata_i[1];
    assign irq_o              = irq_en && (status_done || status_error);

    assign cfg_k_count_m1_o    = cfg_k_count_m1;
    assign cfg_act_stride_m1_o = cfg_act_stride_m1;
    assign act_base_o          = act_base_reg;
    assign wgt_base_o          = wgt_base_reg;
    assign out_base_o          = out_base_reg;
    assign acc_init_o          = acc_init_reg;
    assign out_count_m1_o      = out_count_m1_reg;
    assign out_stride_m1_o     = out_stride_m1_reg;
    assign wgt_stride_m1_o     = wgt_stride_m1_reg;
    assign bias_base_o         = bias_base_reg;
    assign quant_mult_o        = quant_mult_reg;
    assign quant_shift_o       = quant_shift_reg;
    assign out_zero_point_o    = out_zero_point_reg;
    assign activation_mode_o   = activation_mode_reg;
    assign relu6_max_o         = relu6_max_reg;

    always @* begin
        host_rdata_o      = 32'h0000_0000;
        host_error_o      = 1'b0;
        host_error_code_o = ERR_NONE;

        if (reg_access_i) begin
            if (!aligned_i) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_REG_UNALIGNED;
            end else begin
                case (mm_addr_i)
                    ADDR_CTRL: begin
                        host_rdata_o = {29'd0, irq_en, 2'b00};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_STATUS: begin
                        host_rdata_o = {27'd0, busy_i, status_sat_overflow,
                                        status_error, status_done, busy_i};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_CFG: begin
                        host_rdata_o = {1'b1, 15'd0, cfg_act_stride_m1,
                                        cfg_k_count_m1};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_ACT_BASE: begin
                        host_rdata_o = {24'd0, act_base_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_WGT_BASE: begin
                        host_rdata_o = {24'd0, wgt_base_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_OUT_BASE: begin
                        host_rdata_o = {24'd0, out_base_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_ACC_INIT: begin
                        host_rdata_o = acc_init_reg;
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_ACC_RESULT: begin
                        host_rdata_o = acc_result_i;
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end else if (mm_write_i) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_RO_WRITE;
                        end
                    end
                    ADDR_ERR_CODE: begin
                        host_rdata_o = {27'd0, err_code_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_OUT_CFG: begin
                        host_rdata_o = {8'd0, wgt_stride_m1_reg,
                                        out_stride_m1_reg, out_count_m1_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_BIAS_BASE: begin
                        host_rdata_o = {28'd0, bias_base_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_QUANT_MULT: begin
                        host_rdata_o = quant_mult_reg;
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_QUANT_CFG: begin
                        host_rdata_o = {relu6_max_reg, 6'd0,
                                        activation_mode_reg,
                                        out_zero_point_reg, 2'd0,
                                        quant_shift_reg};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end
                    end
                    ADDR_LAST_OUT_COUNT: begin
                        host_rdata_o = {24'd0, last_out_count_i};
                        if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_BAD_REG_WSTRB;
                        end else if (mm_write_i) begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_RO_WRITE;
                        end
                    end
                    default: begin
                        host_error_o      = 1'b1;
                        host_error_code_o = ERR_INVALID_ADDR;
                    end
                endcase
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq_en              <= 1'b0;
            status_done         <= 1'b0;
            status_error        <= 1'b0;
            status_sat_overflow <= 1'b0;
            cfg_k_count_m1      <= 8'h00;
            cfg_act_stride_m1   <= 8'h03;
            act_base_reg        <= 8'h00;
            wgt_base_reg        <= 8'h00;
            out_base_reg        <= 8'h00;
            acc_init_reg        <= 32'h0000_0000;
            err_code_reg        <= ERR_NONE;
            out_count_m1_reg    <= 8'h00;
            out_stride_m1_reg   <= 8'h00;
            wgt_stride_m1_reg   <= 8'h03;
            bias_base_reg       <= 4'h0;
            quant_mult_reg      <= 32'h0000_0001;
            quant_shift_reg     <= 6'h00;
            out_zero_point_reg  <= 8'h00;
            activation_mode_reg <= ACT_NONE;
            relu6_max_reg       <= 8'h7f;
        end else if (soft_reset_pulse_o) begin
            irq_en              <= 1'b0;
            status_done         <= 1'b0;
            status_error        <= 1'b0;
            status_sat_overflow <= 1'b0;
            cfg_k_count_m1      <= 8'h00;
            cfg_act_stride_m1   <= 8'h03;
            act_base_reg        <= 8'h00;
            wgt_base_reg        <= 8'h00;
            out_base_reg        <= 8'h00;
            acc_init_reg        <= 32'h0000_0000;
            err_code_reg        <= ERR_NONE;
            out_count_m1_reg    <= 8'h00;
            out_stride_m1_reg   <= 8'h00;
            wgt_stride_m1_reg   <= 8'h03;
            bias_base_reg       <= 4'h0;
            quant_mult_reg      <= 32'h0000_0001;
            quant_shift_reg     <= 6'h00;
            out_zero_point_reg  <= 8'h00;
            activation_mode_reg <= ACT_NONE;
            relu6_max_reg       <= 8'h7f;
        end else begin
            if (accepted_i && host_error_i) begin
                status_error <= 1'b1;
                err_code_reg <= host_error_code_i;
            end

            if (ctrl_write) begin
                irq_en <= mm_wdata_i[2];
                if (mm_wdata_i[3]) begin
                    status_done <= 1'b0;
                end
                if (mm_wdata_i[4]) begin
                    status_error <= 1'b0;
                    err_code_reg <= ERR_NONE;
                end
            end

            if (status_write) begin
                if (mm_wdata_i[1]) begin
                    status_done <= 1'b0;
                end
                if (mm_wdata_i[2]) begin
                    status_error <= 1'b0;
                    err_code_reg <= ERR_NONE;
                end
                if (mm_wdata_i[3]) begin
                    status_sat_overflow <= 1'b0;
                end
            end

            if (cfg_write) begin
                cfg_k_count_m1    <= mm_wdata_i[7:0];
                cfg_act_stride_m1 <= mm_wdata_i[15:8];
            end
            if (act_base_write) begin
                act_base_reg <= mm_wdata_i[7:0];
            end
            if (wgt_base_write) begin
                wgt_base_reg <= mm_wdata_i[7:0];
            end
            if (out_base_write) begin
                out_base_reg <= mm_wdata_i[7:0];
            end
            if (acc_init_write) begin
                acc_init_reg <= mm_wdata_i;
            end
            if (err_code_write && (mm_wdata_i[4:0] != 5'd0)) begin
                status_error <= 1'b0;
                err_code_reg <= ERR_NONE;
            end
            if (out_cfg_write) begin
                out_count_m1_reg  <= mm_wdata_i[7:0];
                out_stride_m1_reg <= mm_wdata_i[15:8];
                wgt_stride_m1_reg <= mm_wdata_i[23:16];
            end
            if (bias_base_write) begin
                bias_base_reg <= mm_wdata_i[3:0];
            end
            if (quant_mult_write) begin
                quant_mult_reg <= mm_wdata_i;
            end
            if (quant_cfg_write) begin
                quant_shift_reg     <= mm_wdata_i[5:0];
                out_zero_point_reg  <= mm_wdata_i[15:8];
                activation_mode_reg <= mm_wdata_i[17:16];
                relu6_max_reg       <= mm_wdata_i[31:24];
            end

            if (start_pulse_o && busy_i) begin
                status_done  <= 1'b0;
                status_error <= 1'b1;
                err_code_reg <= ERR_START_BUSY;
            end else if (start_pulse_o) begin
                status_done         <= 1'b0;
                status_error        <= 1'b0;
                status_sat_overflow <= 1'b0;
                err_code_reg        <= ERR_NONE;
            end else begin
                if (core_status_error_set_i) begin
                    status_error <= 1'b1;
                    err_code_reg <= core_status_error_code_i;
                end
                if (core_status_sat_overflow_i) begin
                    status_sat_overflow <= 1'b1;
                end
                if (core_status_done_set_i) begin
                    status_done <= 1'b1;
                end
            end
        end
    end

endmodule
