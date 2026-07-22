//============================================================================
// Module     : stories260k
// Function   : stories260K mixed-W4/W8 inference engine (top)
//
// Software-managed decode accelerator for the llama2.c TinyStories stories260K
// checkpoint architecture (dim=64, 5 layers, 8 heads, hidden=172, vocab=512,
// context<=512), mixed-W4/W8 weights and INT4 KV cache with fused dequantization on
// a 64-MAC array. Single clock, low-active async reset, 32-bit MMIO target.
//============================================================================

module stories260k (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        mm_valid,
    input  wire        mm_write,
    input  wire [19:0] mm_addr,
    input  wire [31:0] mm_wdata,
    input  wire [3:0]  mm_wstrb,
    output reg  [31:0] mm_rdata,
    output wire        mm_ready,
    output reg         mm_error,
    output wire        irq
);

    localparam [19:0] WBUF_BASE = 20'h10000;
    localparam [19:0] WBUF_END  = 20'h373FF;   // 157 KiB (5024 x 32B; v1.7 +WO2+WQ3 INT8)
    localparam [19:0] KV_BASE   = 20'h40000;
    localparam [19:0] KV_END    = 20'h5EFFF;   // 124 KiB
    localparam [19:0] ACT_BASE  = 20'h60000;
    localparam [19:0] ACT_END   = 20'h60FFF;   // 4 KiB
    localparam [19:0] VEC_BASE  = 20'h64000;
    localparam [19:0] VEC_END   = 20'h65FFF;   // 8 KiB

    localparam [3:0] ERR_INVALID_ADDR = 4'd5;

    wire        reg_region  = (mm_addr < 20'h01000);
    wire        wbuf_window = (mm_addr >= WBUF_BASE) && (mm_addr <= WBUF_END);
    wire        kv_window   = (mm_addr >= KV_BASE)   && (mm_addr <= KV_END);
    wire        act_window  = (mm_addr >= ACT_BASE)  && (mm_addr <= ACT_END);
    wire        vec_window  = (mm_addr >= VEC_BASE)  && (mm_addr <= VEC_END);
    wire        spm_window  = wbuf_window || kv_window || act_window ||
                              vec_window;
    wire        busy;
    wire        spm_stall   = mm_valid && spm_window && busy;
    assign      mm_ready    = !spm_stall;
    wire        accepted    = mm_valid && mm_ready;
    wire        aligned     = (mm_addr[1:0] == 2'b00);

    wire [3:0]  host_sel = {vec_window, act_window, kv_window, wbuf_window};
    // 32-bit word address inside the window (buffer [1:0] bits are ignored
    // by contract; see docs/interface_spec.md)
    wire [15:0] host_addr = wbuf_window ? (mm_addr[17:2] - 16'h4000) :
                            kv_window   ?  mm_addr[17:2] :
                            act_window  ? (mm_addr[17:2] - 16'h8000) :
                                          (mm_addr[17:2] - 16'h9000);

    wire [31:0] regs_rdata;
    wire        regs_error;
    wire [3:0]  regs_error_code;
    wire [31:0] spm_wbuf_rdata, spm_kv_rdata, spm_act_rdata, spm_vec_rdata;

    reg [31:0] host_rdata;
    reg        host_error;
    reg [3:0]  host_error_code;

    always @* begin
        host_rdata      = 32'h0000_0000;
        host_error      = 1'b0;
        host_error_code = 4'd0;
        if (accepted) begin
            if (reg_region) begin
                host_rdata      = regs_rdata;
                host_error      = regs_error;
                host_error_code = regs_error_code;
            end else if (wbuf_window) begin
                host_rdata = spm_wbuf_rdata;
            end else if (kv_window) begin
                host_rdata = spm_kv_rdata;
            end else if (act_window) begin
                host_rdata = spm_act_rdata;
            end else if (vec_window) begin
                host_rdata = spm_vec_rdata;
            end else begin
                host_error      = 1'b1;
                host_error_code = ERR_INVALID_ADDR;
            end
        end
    end

    wire soft_reset_pulse;
    wire start_pulse;

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

    // ---------------- core <-> spm wires ----------------
    wire [12:0]  wbuf_raddr;
    wire [255:0] wbuf_rdata;
    wire [12:0]  wbuf_saddr;
    wire [255:0] wbuf_sdata;
    wire [12:0]  wbuf_i8_raddr;
    wire [255:0] wbuf_i8_rdata;
    wire [11:0]  kv_raddr;
    wire [255:0] kv_rdata, kv_vdata;
    wire [11:0]  kv_scale_raddr;
    wire [255:0] kv_scale_rdata;
    wire         kv_we;
    wire [11:0]  kv_waddr;
    wire [255:0] kv_wdata;
    wire [31:0]  kv_wstrb;
    wire [8:0]   act_raddr;
    wire [63:0]  act_rdata;
    wire         act_we;
    wire [8:0]   act_waddr;
    wire [63:0]  act_wdata;
    wire [7:0]   act_wstrb;
    wire [9:0]   vec_raddr;
    wire [63:0]  vec_rdata;
    wire         vec_we;
    wire [9:0]   vec_waddr;
    wire [63:0]  vec_wdata;
    wire [7:0]   vec_wstrb;

    // ---------------- regs <-> core wires ----------------
    wire        done_set, error_set, token_valid_set, token_inc;
    wire [3:0]  error_code;
    wire [8:0]  token_out;
    wire [9:0]  seq_pos;
    wire        cycle_en;
    wire [6:0]  mac_adv;
    wire [8:0]  cfg_token_in, cfg_gen_len;
    wire        cfg_chain_en;
    wire [3:0]  cfg_sm_shift;
    wire [7:0]  cfg_rep_pen;
    wire        cfg_adapt_en;
    wire [3:0]  cfg_norep_win;

    stories260k_regs u_regs (
        .clk                (clk),
        .rst_n              (rst_n),
        .accepted_i         (accepted),
        .reg_access_i       (accepted && reg_region),
        .mm_write_i         (mm_write),
        .mm_addr_i          (mm_addr),
        .mm_wdata_i         (mm_wdata),
        .aligned_i          (aligned),
        .busy_i             (busy),
        .host_error_i       (host_error),
        .host_error_code_i  (host_error_code),
        .done_set_i         (done_set),
        .error_set_i        (error_set),
        .error_code_i       (error_code),
        .token_valid_set_i  (token_valid_set),
        .token_out_i        (token_out),
        .seq_pos_i          (seq_pos),
        .cycle_en_i         (cycle_en),
        .token_inc_i        (token_inc),
        .mac_adv_i          (mac_adv),
        .host_rdata_o       (regs_rdata),
        .host_error_o       (regs_error),
        .host_error_code_o  (regs_error_code),
        .start_pulse_o      (start_pulse),
        .soft_reset_pulse_o (soft_reset_pulse),
        .irq_o              (irq),
        .cfg_token_in_o     (cfg_token_in),
        .cfg_gen_len_o      (cfg_gen_len),
        .cfg_chain_en_o     (cfg_chain_en),
        .cfg_sm_shift_o     (cfg_sm_shift),
        .cfg_rep_pen_o      (cfg_rep_pen),
        .cfg_adapt_en_o     (cfg_adapt_en),
        .cfg_norep_win_o    (cfg_norep_win)
    );

    stories260k_spm u_spm (
        .clk               (clk),
        .host_sel_i        (host_sel),
        .host_we_i         (accepted && spm_window && mm_write),
        .host_addr_i       (host_addr),
        .host_wdata_i      (mm_wdata),
        .host_wstrb_i      (mm_wstrb),
        .host_wbuf_rdata_o (spm_wbuf_rdata),
        .host_kv_rdata_o   (spm_kv_rdata),
        .host_act_rdata_o  (spm_act_rdata),
        .host_vec_rdata_o  (spm_vec_rdata),
        .wbuf_raddr_i      (wbuf_raddr),
        .wbuf_rdata_o      (wbuf_rdata),
        .wbuf_saddr_i      (wbuf_saddr),
        .wbuf_sdata_o      (wbuf_sdata),
        .wbuf_i8_raddr_i   (wbuf_i8_raddr),
        .wbuf_i8_rdata_o   (wbuf_i8_rdata),
        .kv_raddr_i        (kv_raddr),
        .kv_rdata_o        (kv_rdata),
        .kv_vdata_o        (kv_vdata),
        .kv_scale_raddr_i  (kv_scale_raddr),
        .kv_scale_rdata_o  (kv_scale_rdata),
        .kv_we_i           (kv_we),
        .kv_waddr_i        (kv_waddr),
        .kv_wdata_i        (kv_wdata),
        .kv_wstrb_i        (kv_wstrb),
        .act_raddr_i       (act_raddr),
        .act_rdata_o       (act_rdata),
        .act_we_i          (act_we),
        .act_waddr_i       (act_waddr),
        .act_wdata_i       (act_wdata),
        .act_wstrb_i       (act_wstrb),
        .vec_raddr_i       (vec_raddr),
        .vec_rdata_o       (vec_rdata),
        .vec_we_i          (vec_we),
        .vec_waddr_i       (vec_waddr),
        .vec_wdata_i       (vec_wdata),
        .vec_wstrb_i       (vec_wstrb)
    );

    stories260k_core u_core (
        .clk                (clk),
        .rst_n              (rst_n),
        .soft_reset_i       (soft_reset_pulse),
        .start_pulse_i      (start_pulse),
        .cfg_token_in_i     (cfg_token_in),
        .cfg_gen_len_i      (cfg_gen_len),
        .cfg_chain_en_i     (cfg_chain_en),
        .cfg_sm_shift_i     (cfg_sm_shift),
        .cfg_rep_pen_i      (cfg_rep_pen),
        .cfg_adapt_en_i     (cfg_adapt_en),
        .cfg_norep_win_i    (cfg_norep_win),
        .busy_o             (busy),
        .done_set_o         (done_set),
        .error_set_o        (error_set),
        .error_code_o       (error_code),
        .token_valid_set_o  (token_valid_set),
        .token_out_o        (token_out),
        .seq_pos_o          (seq_pos),
        .cycle_en_o         (cycle_en),
        .token_inc_o        (token_inc),
        .mac_adv_o          (mac_adv),
        .wbuf_raddr_o       (wbuf_raddr),
        .wbuf_rdata_i       (wbuf_rdata),
        .wbuf_saddr_o       (wbuf_saddr),
        .wbuf_sdata_i       (wbuf_sdata),
        .wbuf_i8_raddr_o    (wbuf_i8_raddr),
        .wbuf_i8_rdata_i    (wbuf_i8_rdata),
        .kv_raddr_o         (kv_raddr),
        .kv_rdata_i         (kv_rdata),
        .kv_vdata_i         (kv_vdata),
        .kv_scale_raddr_o   (kv_scale_raddr),
        .kv_scale_rdata_i   (kv_scale_rdata),
        .kv_we_o            (kv_we),
        .kv_waddr_o         (kv_waddr),
        .kv_wdata_o         (kv_wdata),
        .kv_wstrb_o         (kv_wstrb),
        .act_raddr_o        (act_raddr),
        .act_rdata_i        (act_rdata),
        .act_we_o           (act_we),
        .act_waddr_o        (act_waddr),
        .act_wdata_o        (act_wdata),
        .act_wstrb_o        (act_wstrb),
        .vec_raddr_o        (vec_raddr),
        .vec_rdata_i        (vec_rdata),
        .vec_we_o           (vec_we),
        .vec_waddr_o        (vec_waddr),
        .vec_wdata_o        (vec_wdata),
        .vec_wstrb_o        (vec_wstrb)
    );

endmodule
