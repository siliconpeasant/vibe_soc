//============================================================================
// Module     : stories260k_regs
// Function   : CSR file, sticky status, and performance counters
//============================================================================

module stories260k_regs (
    input  wire        clk,
    input  wire        rst_n,

    input  wire        accepted_i,
    input  wire        reg_access_i,
    input  wire        mm_write_i,
    input  wire [19:0] mm_addr_i,
    input  wire [31:0] mm_wdata_i,
    input  wire        aligned_i,
    input  wire        busy_i,
    input  wire        host_error_i,   // any MMIO access error (top level)
    input  wire [3:0]  host_error_code_i,

    // Core status events
    input  wire        done_set_i,
    input  wire        error_set_i,
    input  wire [3:0]  error_code_i,
    input  wire        token_valid_set_i,
    input  wire [8:0]  token_out_i,
    input  wire [9:0]  seq_pos_i,

    // Performance counter strobes
    input  wire        cycle_en_i,
    input  wire        token_inc_i,
    input  wire [6:0]  mac_adv_i,

    output reg  [31:0] host_rdata_o,
    output reg         host_error_o,
    output reg  [3:0]  host_error_code_o,

    output reg         start_pulse_o,
    output reg         soft_reset_pulse_o,
    output wire        irq_o,
    output wire [8:0]  cfg_token_in_o,
    output wire [8:0]  cfg_gen_len_o,
    output wire        cfg_chain_en_o,
    output wire [3:0]  cfg_sm_shift_o
);

    localparam [31:0] ID_VALUE      = 32'h5354_4F52; // "STOR"
    localparam [31:0] VERSION_VALUE = 32'h0001_0000;

    localparam [11:0] OFF_ID       = 12'h000;
    localparam [11:0] OFF_VERSION  = 12'h004;
    localparam [11:0] OFF_CTRL     = 12'h008;
    localparam [11:0] OFF_STATUS   = 12'h00C;
    localparam [11:0] OFF_TOKEN_IN = 12'h010;
    localparam [11:0] OFF_TOKEN_O  = 12'h014;
    localparam [11:0] OFF_SEQ_POS  = 12'h018;
    localparam [11:0] OFF_GEN_CFG  = 12'h01C;
    localparam [11:0] OFF_CYCLE_LO = 12'h020;
    localparam [11:0] OFF_CYCLE_HI = 12'h024;
    localparam [11:0] OFF_TOKEN_CT = 12'h028;
    localparam [11:0] OFF_MAC_LO   = 12'h02C;
    localparam [11:0] OFF_MAC_HI   = 12'h030;
    localparam [11:0] OFF_PERF_CLR = 12'h034;
    localparam [11:0] OFF_ERR_ADDR = 12'h03C;

    localparam [3:0] ERR_NONE        = 4'd0;
    localparam [3:0] ERR_ALIGN       = 4'd1;
    localparam [3:0] ERR_RO_WRITE    = 4'd2;
    localparam [3:0] ERR_BUSY_START  = 4'd3;
    localparam [3:0] ERR_INVALID_ADDR = 4'd5;

    reg        irq_en;
    reg        chain_en;
    reg [8:0]  token_in;
    reg [8:0]  gen_len_m1;
    reg [3:0]  sm_shift;
    reg        st_done;
    reg        st_error;
    reg        st_token_valid;
    reg [3:0]  ecode;
    reg [19:0] err_addr;
    reg [3:0]  err_code;
    reg [63:0] cycle_cnt;
    reg [31:0] token_cnt;
    reg [63:0] mac_cnt;

    // MMIO write data is 32-bit by interface contract; fields above bit 8
    // are intentionally not mapped to any register.
    wire [22:0] unused_wdata_hi = mm_wdata_i[31:9];

    wire [11:0] offset = mm_addr_i[11:0];
    wire        perf_clear;

    assign cfg_token_in_o = token_in;
    assign cfg_gen_len_o  = gen_len_m1;
    assign cfg_chain_en_o = chain_en;
    assign cfg_sm_shift_o = sm_shift;
    assign irq_o          = irq_en & (st_done | st_error | st_token_valid);
    assign perf_clear     = accepted_i && reg_access_i && mm_write_i &&
                            aligned_i && (offset == OFF_PERF_CLR);

    // ------------------------------------------------------------------
    // Control/status state
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq_en          <= 1'b0;
            chain_en        <= 1'b0;
            token_in        <= 9'd0;
            gen_len_m1      <= 9'd0;
            sm_shift        <= 4'd2;
            st_done         <= 1'b0;
            st_error        <= 1'b0;
            st_token_valid  <= 1'b0;
            ecode           <= ERR_NONE;
            err_addr        <= 20'd0;
            err_code        <= ERR_NONE;
            start_pulse_o       <= 1'b0;
            soft_reset_pulse_o  <= 1'b0;
        end else if (soft_reset_pulse_o) begin
            irq_en          <= 1'b0;
            chain_en        <= 1'b0;
            token_in        <= 9'd0;
            gen_len_m1      <= 9'd0;
            sm_shift        <= 4'd2;
            st_done         <= 1'b0;
            st_error        <= 1'b0;
            st_token_valid  <= 1'b0;
            ecode           <= ERR_NONE;
            err_addr        <= 20'd0;
            err_code        <= ERR_NONE;
            start_pulse_o       <= 1'b0;
            soft_reset_pulse_o  <= 1'b0;
        end else begin
            start_pulse_o      <= 1'b0;
            soft_reset_pulse_o <= 1'b0;

            if (done_set_i)        st_done        <= 1'b1;
            if (token_valid_set_i) st_token_valid <= 1'b1;
            if (error_set_i) begin
                st_error <= 1'b1;
                ecode    <= error_code_i;
            end
            if (host_error_i) begin
                err_addr <= mm_addr_i;
                err_code <= host_error_code_i;
            end

            if (accepted_i && reg_access_i && mm_write_i && aligned_i) begin
                case (offset)
                    OFF_CTRL: begin
                        if (mm_wdata_i[0] && !busy_i) begin
                            start_pulse_o <= 1'b1;
                            st_done       <= 1'b0;
                            st_error      <= 1'b0;
                            ecode         <= ERR_NONE;
                        end
                        if (mm_wdata_i[1])
                            soft_reset_pulse_o <= 1'b1;
                        irq_en   <= mm_wdata_i[2];
                        chain_en <= mm_wdata_i[3];
                    end
                    OFF_STATUS: begin
                        if (mm_wdata_i[1]) st_done        <= 1'b0;
                        if (mm_wdata_i[2]) st_error       <= 1'b0;
                        if (mm_wdata_i[8]) st_token_valid <= 1'b0;
                    end
                    OFF_TOKEN_IN: token_in   <= mm_wdata_i[8:0];
                    OFF_GEN_CFG: begin
                        gen_len_m1 <= mm_wdata_i[8:0];
                        sm_shift   <= mm_wdata_i[20:17];
                    end
                    default: ;
                endcase
            end
        end
    end

    // ------------------------------------------------------------------
    // Performance counters
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cycle_cnt <= 64'd0;
            token_cnt <= 32'd0;
            mac_cnt   <= 64'd0;
        end else if (soft_reset_pulse_o || perf_clear) begin
            cycle_cnt <= 64'd0;
            token_cnt <= 32'd0;
            mac_cnt   <= 64'd0;
        end else begin
            if (cycle_en_i) cycle_cnt <= cycle_cnt + 64'd1;
            if (token_inc_i) token_cnt <= token_cnt + 32'd1;
            mac_cnt <= mac_cnt + {57'd0, mac_adv_i};
        end
    end

    // ------------------------------------------------------------------
    // Readback and access-error decode
    // ------------------------------------------------------------------
    always @* begin
        host_rdata_o      = 32'h0000_0000;
        host_error_o      = 1'b0;
        host_error_code_o = ERR_NONE;

        if (accepted_i && reg_access_i) begin
            if (!aligned_i) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_ALIGN;
            end else begin
                case (offset)
                    OFF_ID:       host_rdata_o = ID_VALUE;
                    OFF_VERSION:  host_rdata_o = VERSION_VALUE;
                    OFF_CTRL:     host_rdata_o = {28'd0, chain_en, irq_en, 2'b00};
                    OFF_STATUS:   host_rdata_o = {23'd0, st_token_valid,
                                                  ecode[3:0], 1'b0, st_error,
                                                  st_done, busy_i};
                    OFF_TOKEN_IN: host_rdata_o = {23'd0, token_in};
                    OFF_TOKEN_O:  host_rdata_o = {23'd0, token_out_i};
                    OFF_SEQ_POS:  host_rdata_o = {22'd0, seq_pos_i};
                    OFF_GEN_CFG:  host_rdata_o = {12'd0, sm_shift, 7'd0, gen_len_m1};
                    OFF_CYCLE_LO: host_rdata_o = cycle_cnt[31:0];
                    OFF_CYCLE_HI: host_rdata_o = cycle_cnt[63:32];
                    OFF_TOKEN_CT: host_rdata_o = token_cnt;
                    OFF_MAC_LO:   host_rdata_o = mac_cnt[31:0];
                    OFF_MAC_HI:   host_rdata_o = mac_cnt[63:32];
                    OFF_ERR_ADDR: host_rdata_o = {8'd0, err_code, err_addr};
                    default: begin
                        host_error_o      = 1'b1;
                        host_error_code_o = ERR_INVALID_ADDR;
                    end
                endcase

                if (mm_write_i) begin
                    case (offset)
                        OFF_CTRL, OFF_STATUS, OFF_TOKEN_IN,
                        OFF_GEN_CFG, OFF_PERF_CLR: ;
                        OFF_ID, OFF_VERSION, OFF_TOKEN_O, OFF_SEQ_POS,
                        OFF_CYCLE_LO, OFF_CYCLE_HI, OFF_TOKEN_CT,
                        OFF_MAC_LO, OFF_MAC_HI, OFF_ERR_ADDR: begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_RO_WRITE;
                        end
                        default: begin
                            host_error_o      = 1'b1;
                            host_error_code_o = ERR_INVALID_ADDR;
                        end
                    endcase
                end
            end

            if (mm_write_i && aligned_i && (offset == OFF_CTRL) &&
                mm_wdata_i[0] && busy_i) begin
                host_error_o      = 1'b1;
                host_error_code_o = ERR_BUSY_START;
            end
        end
    end

endmodule
