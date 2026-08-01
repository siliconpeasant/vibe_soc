//============================================================================
// Module     : npu_spm
// Function   : Activation, weight, output, and bias scratchpads
//============================================================================

module npu_spm #(
    parameter integer ACT_SPM_BYTES  = 64,
    parameter integer WGT_SPM_BYTES  = 64,
    parameter integer OUT_SPM_BYTES  = 64,
    parameter integer BIAS_SPM_WORDS = 16
) (
    input         clk,
    input         rst_n,
    input         soft_reset_i,
    input         access_i,
    input         mm_write_i,
    input  [31:0] mm_wdata_i,
    input  [3:0]  mm_wstrb_i,
    input         aligned_i,
    input         act_window_i,
    input         wgt_window_i,
    input         out_window_i,
    input         bias_window_i,
    input  [5:0]  byte_offset_i,
    input  [3:0]  bias_index_i,
    input         host_error_i,
    output reg [31:0] host_rdata_o,
    output reg        host_error_o,
    output reg [4:0]  host_error_code_o,
    input  [5:0]      act_rd_addr_i,
    input  [5:0]      wgt_rd_addr_i,
    input  [3:0]      bias_rd_addr_i,
    output [31:0]     act_word_o,
    output [31:0]     wgt_word_o,
    output [31:0]     bias_word_o,
    input             out_wr_en_i,
    input  [5:0]      out_wr_addr_i,
    input  [7:0]      out_wr_data_i
);

    localparam ERR_NONE           = 5'd0;
    localparam ERR_INVALID_ADDR   = 5'd5;
    localparam ERR_SPM_UNALIGNED  = 5'd8;
    localparam ERR_BIAS_BAD_WSTRB = 5'd13;

    localparam [6:0] ACT_SPM_BYTES_VALUE  = ACT_SPM_BYTES[6:0];
    localparam [6:0] WGT_SPM_BYTES_VALUE  = WGT_SPM_BYTES[6:0];
    localparam [6:0] OUT_SPM_BYTES_VALUE  = OUT_SPM_BYTES[6:0];
    localparam [4:0] BIAS_SPM_WORDS_VALUE = BIAS_SPM_WORDS[4:0];

    localparam integer ACT_SPM_DEPTH = ACT_SPM_BYTES / 4;
    localparam integer WGT_SPM_DEPTH = WGT_SPM_BYTES / 4;
    localparam integer OUT_SPM_DEPTH = OUT_SPM_BYTES / 4;

    reg [7:0]  act_spm_lane0 [0:ACT_SPM_DEPTH-1];
    reg [7:0]  act_spm_lane1 [0:ACT_SPM_DEPTH-1];
    reg [7:0]  act_spm_lane2 [0:ACT_SPM_DEPTH-1];
    reg [7:0]  act_spm_lane3 [0:ACT_SPM_DEPTH-1];
    reg [7:0]  wgt_spm_lane0 [0:WGT_SPM_DEPTH-1];
    reg [7:0]  wgt_spm_lane1 [0:WGT_SPM_DEPTH-1];
    reg [7:0]  wgt_spm_lane2 [0:WGT_SPM_DEPTH-1];
    reg [7:0]  wgt_spm_lane3 [0:WGT_SPM_DEPTH-1];
    reg [7:0]  out_spm_lane0 [0:OUT_SPM_DEPTH-1];
    reg [7:0]  out_spm_lane1 [0:OUT_SPM_DEPTH-1];
    reg [7:0]  out_spm_lane2 [0:OUT_SPM_DEPTH-1];
    reg [7:0]  out_spm_lane3 [0:OUT_SPM_DEPTH-1];
    reg [31:0] bias_spm [0:BIAS_SPM_WORDS-1];

    integer i;

    wire [6:0] byte_word_last;
    wire       act_access_valid;
    wire       wgt_access_valid;
    wire       out_access_valid;
    wire       bias_access_valid;
    wire [5:0] act_host_rd_addr;
    wire [5:0] wgt_host_rd_addr;
    wire [5:0] act_array_rd_addr;
    wire [5:0] wgt_array_rd_addr;
    wire [3:0] bias_array_rd_addr;
    wire [3:0] act_array_word_addr;
    wire [3:0] wgt_array_word_addr;
    wire [3:0] out_array_word_addr;
    wire [3:0] act_lane0_rd_addr;
    wire [3:0] act_lane1_rd_addr;
    wire [3:0] act_lane2_rd_addr;
    wire [3:0] act_lane3_rd_addr;
    wire [3:0] wgt_lane0_rd_addr;
    wire [3:0] wgt_lane1_rd_addr;
    wire [3:0] wgt_lane2_rd_addr;
    wire [3:0] wgt_lane3_rd_addr;
    wire [31:0] act_bank_data;
    wire [31:0] wgt_bank_data;
    wire [31:0] out_host_word;

    function [31:0] rotate_bank_data;
        input [31:0] bank_data;
        input [1:0]  first_lane;
        begin
            case (first_lane)
                2'd0: rotate_bank_data = bank_data;
                2'd1: rotate_bank_data = {bank_data[7:0],
                                           bank_data[31:8]};
                2'd2: rotate_bank_data = {bank_data[15:0],
                                           bank_data[31:16]};
                default:
                      rotate_bank_data = {bank_data[23:0],
                                           bank_data[31:24]};
            endcase
        end
    endfunction

    assign byte_word_last   = {1'b0, byte_offset_i} + 7'd3;
    assign act_access_valid = (byte_word_last < ACT_SPM_BYTES_VALUE);
    assign wgt_access_valid = (byte_word_last < WGT_SPM_BYTES_VALUE);
    assign out_access_valid = (byte_word_last < OUT_SPM_BYTES_VALUE);
    assign bias_access_valid =
        ({1'b0, bias_index_i} < BIAS_SPM_WORDS_VALUE);

    assign act_host_rd_addr = act_access_valid ? byte_offset_i : 6'd0;
    assign wgt_host_rd_addr = wgt_access_valid ? byte_offset_i : 6'd0;
    assign act_array_rd_addr = (access_i && act_window_i) ?
                                act_host_rd_addr : act_rd_addr_i;
    assign wgt_array_rd_addr = (access_i && wgt_window_i) ?
                                wgt_host_rd_addr : wgt_rd_addr_i;
    assign bias_array_rd_addr = (access_i && bias_window_i) ?
                                 (bias_access_valid ? bias_index_i : 4'd0) :
                                 bias_rd_addr_i;

    assign act_array_word_addr = act_array_rd_addr[5:2];
    assign wgt_array_word_addr = wgt_array_rd_addr[5:2];
    assign out_array_word_addr = out_access_valid ?
                                  byte_offset_i[5:2] : 4'd0;

    // A four-byte compute fetch touches each byte lane bank exactly once.
    // Banks below the first lane advance to the following aligned word.
    assign act_lane0_rd_addr = act_array_word_addr +
                               {3'd0, |act_array_rd_addr[1:0]};
    assign act_lane1_rd_addr = act_array_word_addr +
                               {3'd0, act_array_rd_addr[1]};
    assign act_lane2_rd_addr = act_array_word_addr +
                               {3'd0, &act_array_rd_addr[1:0]};
    assign act_lane3_rd_addr = act_array_word_addr;
    assign wgt_lane0_rd_addr = wgt_array_word_addr +
                               {3'd0, |wgt_array_rd_addr[1:0]};
    assign wgt_lane1_rd_addr = wgt_array_word_addr +
                               {3'd0, wgt_array_rd_addr[1]};
    assign wgt_lane2_rd_addr = wgt_array_word_addr +
                               {3'd0, &wgt_array_rd_addr[1:0]};
    assign wgt_lane3_rd_addr = wgt_array_word_addr;

    assign act_bank_data = {act_spm_lane3[act_lane3_rd_addr],
                            act_spm_lane2[act_lane2_rd_addr],
                            act_spm_lane1[act_lane1_rd_addr],
                            act_spm_lane0[act_lane0_rd_addr]};
    assign wgt_bank_data = {wgt_spm_lane3[wgt_lane3_rd_addr],
                            wgt_spm_lane2[wgt_lane2_rd_addr],
                            wgt_spm_lane1[wgt_lane1_rd_addr],
                            wgt_spm_lane0[wgt_lane0_rd_addr]};
    assign out_host_word = {out_spm_lane3[out_array_word_addr],
                            out_spm_lane2[out_array_word_addr],
                            out_spm_lane1[out_array_word_addr],
                            out_spm_lane0[out_array_word_addr]};

    generate
        if ((ACT_SPM_BYTES < 4) || (ACT_SPM_BYTES > 64) ||
            ((ACT_SPM_BYTES % 4) != 0) ||
            (WGT_SPM_BYTES < 4) || (WGT_SPM_BYTES > 64) ||
            ((WGT_SPM_BYTES % 4) != 0) ||
            (OUT_SPM_BYTES < 4) || (OUT_SPM_BYTES > 64) ||
            ((OUT_SPM_BYTES % 4) != 0) ||
            (BIAS_SPM_WORDS < 1) || (BIAS_SPM_WORDS > 16)) begin : g_invalid_parameters
            initial begin
                $display("ERROR: illegal npu_spm capacity parameter");
                $finish;
            end
        end
    endgenerate

    assign act_word_o = rotate_bank_data(act_bank_data,
                                         act_array_rd_addr[1:0]);
    assign wgt_word_o = rotate_bank_data(wgt_bank_data,
                                         wgt_array_rd_addr[1:0]);
    assign bias_word_o = bias_spm[bias_array_rd_addr];

    always @* begin
        host_rdata_o      = 32'h0000_0000;
        host_error_o      = 1'b0;
        host_error_code_o = ERR_NONE;

        if (access_i) begin
            if (!aligned_i) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_SPM_UNALIGNED;
            end else if (bias_window_i && !bias_access_valid) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_INVALID_ADDR;
            end else if (act_window_i && !act_access_valid) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_INVALID_ADDR;
            end else if (wgt_window_i && !wgt_access_valid) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_INVALID_ADDR;
            end else if (out_window_i && !out_access_valid) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_INVALID_ADDR;
            end else if (bias_window_i) begin
                host_rdata_o = bias_word_o;
                if (mm_write_i && (mm_wstrb_i != 4'b1111)) begin
                    host_error_o      = 1'b1;
                    host_error_code_o = ERR_BIAS_BAD_WSTRB;
                end
            end else if (act_window_i) begin
                host_rdata_o = act_word_o;
            end else if (wgt_window_i) begin
                host_rdata_o = wgt_word_o;
            end else if (out_window_i) begin
                host_rdata_o = out_host_word;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < ACT_SPM_DEPTH; i = i + 1) begin
                act_spm_lane0[i] <= 8'h00;
                act_spm_lane1[i] <= 8'h00;
                act_spm_lane2[i] <= 8'h00;
                act_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < WGT_SPM_DEPTH; i = i + 1) begin
                wgt_spm_lane0[i] <= 8'h00;
                wgt_spm_lane1[i] <= 8'h00;
                wgt_spm_lane2[i] <= 8'h00;
                wgt_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < OUT_SPM_DEPTH; i = i + 1) begin
                out_spm_lane0[i] <= 8'h00;
                out_spm_lane1[i] <= 8'h00;
                out_spm_lane2[i] <= 8'h00;
                out_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < BIAS_SPM_WORDS; i = i + 1) begin
                bias_spm[i] <= 32'h0000_0000;
            end
        end else if (soft_reset_i) begin
            for (i = 0; i < ACT_SPM_DEPTH; i = i + 1) begin
                act_spm_lane0[i] <= 8'h00;
                act_spm_lane1[i] <= 8'h00;
                act_spm_lane2[i] <= 8'h00;
                act_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < WGT_SPM_DEPTH; i = i + 1) begin
                wgt_spm_lane0[i] <= 8'h00;
                wgt_spm_lane1[i] <= 8'h00;
                wgt_spm_lane2[i] <= 8'h00;
                wgt_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < OUT_SPM_DEPTH; i = i + 1) begin
                out_spm_lane0[i] <= 8'h00;
                out_spm_lane1[i] <= 8'h00;
                out_spm_lane2[i] <= 8'h00;
                out_spm_lane3[i] <= 8'h00;
            end
            for (i = 0; i < BIAS_SPM_WORDS; i = i + 1) begin
                bias_spm[i] <= 32'h0000_0000;
            end
        end else begin
            if (access_i && mm_write_i && !host_error_i && aligned_i) begin
                if (act_window_i) begin
                    if (mm_wstrb_i[0]) begin
                        act_spm_lane0[byte_offset_i[5:2]] <=
                            mm_wdata_i[7:0];
                    end
                    if (mm_wstrb_i[1]) begin
                        act_spm_lane1[byte_offset_i[5:2]] <=
                            mm_wdata_i[15:8];
                    end
                    if (mm_wstrb_i[2]) begin
                        act_spm_lane2[byte_offset_i[5:2]] <=
                            mm_wdata_i[23:16];
                    end
                    if (mm_wstrb_i[3]) begin
                        act_spm_lane3[byte_offset_i[5:2]] <=
                            mm_wdata_i[31:24];
                    end
                end else if (wgt_window_i) begin
                    if (mm_wstrb_i[0]) begin
                        wgt_spm_lane0[byte_offset_i[5:2]] <=
                            mm_wdata_i[7:0];
                    end
                    if (mm_wstrb_i[1]) begin
                        wgt_spm_lane1[byte_offset_i[5:2]] <=
                            mm_wdata_i[15:8];
                    end
                    if (mm_wstrb_i[2]) begin
                        wgt_spm_lane2[byte_offset_i[5:2]] <=
                            mm_wdata_i[23:16];
                    end
                    if (mm_wstrb_i[3]) begin
                        wgt_spm_lane3[byte_offset_i[5:2]] <=
                            mm_wdata_i[31:24];
                    end
                end else if (out_window_i) begin
                    if (mm_wstrb_i[0]) begin
                        out_spm_lane0[byte_offset_i[5:2]] <=
                            mm_wdata_i[7:0];
                    end
                    if (mm_wstrb_i[1]) begin
                        out_spm_lane1[byte_offset_i[5:2]] <=
                            mm_wdata_i[15:8];
                    end
                    if (mm_wstrb_i[2]) begin
                        out_spm_lane2[byte_offset_i[5:2]] <=
                            mm_wdata_i[23:16];
                    end
                    if (mm_wstrb_i[3]) begin
                        out_spm_lane3[byte_offset_i[5:2]] <=
                            mm_wdata_i[31:24];
                    end
                end else if (bias_window_i) begin
                    bias_spm[bias_index_i] <= mm_wdata_i;
                end
            end

            if (out_wr_en_i) begin
                case (out_wr_addr_i[1:0])
                    2'd0: out_spm_lane0[out_wr_addr_i[5:2]] <=
                              out_wr_data_i;
                    2'd1: out_spm_lane1[out_wr_addr_i[5:2]] <=
                              out_wr_data_i;
                    2'd2: out_spm_lane2[out_wr_addr_i[5:2]] <=
                              out_wr_data_i;
                    default:
                          out_spm_lane3[out_wr_addr_i[5:2]] <=
                              out_wr_data_i;
                endcase
            end
        end
    end

endmodule
