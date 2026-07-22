//============================================================================
// Module     : stories260k_core
// Function   : Decode sequencer + matrix-vector-multiply engine + argmax
//
// Executes the llama2.c stories260K forward pass one token per iteration:
//   embed -> x5 [rms1 -> qkv -> rope -> kv append -> 8x fused attention
//   -> wo -> res -> rms2 -> w1/w3 -> swiglu -> w2 -> res]
//   -> final rms -> tied-embedding logits with streaming argmax -> token.
//
// All matmuls run on the shared 8x8 MAC array (stories260k_mac); vector ops
// run on the SFU (stories260k_sfu). Weight tiles are stored 8x8-interleaved
// so one 256-bit WBUF word feeds one MAC cycle; see docs/design_spec.md.
//============================================================================

module stories260k_core (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         soft_reset_i,
    input  wire         start_pulse_i,
    input  wire [8:0]   cfg_token_in_i,
    input  wire [8:0]   cfg_gen_len_i,
    input  wire         cfg_chain_en_i,
    input  wire [3:0]   cfg_sm_shift_i,
    input  wire [7:0]   cfg_rep_pen_i,
    input  wire         cfg_adapt_en_i,
    input  wire [3:0]   cfg_norep_win_i,

    output wire         busy_o,
    output reg          done_set_o,
    output reg          error_set_o,
    output reg  [3:0]   error_code_o,
    output reg          token_valid_set_o,
    output reg  [8:0]   token_out_o,
    output reg  [9:0]   seq_pos_o,
    output wire         cycle_en_o,
    output reg          token_inc_o,
    output wire [6:0]   mac_adv_o,
    output wire [12:0]  wbuf_raddr_o,
    input  wire [255:0] wbuf_rdata_i,
    output wire [12:0]  wbuf_saddr_o,
    input  wire [255:0] wbuf_sdata_i,
    output wire [12:0]  wbuf_i8_raddr_o,
    input  wire [255:0] wbuf_i8_rdata_i,
    // KVBUF
    output wire [11:0]  kv_raddr_o,
    input  wire [255:0] kv_rdata_i,
    input  wire [255:0] kv_vdata_i,
    output wire [11:0]  kv_scale_raddr_o,
    input  wire [255:0] kv_scale_rdata_i,
    output wire         kv_we_o,
    output wire [11:0]  kv_waddr_o,
    output wire [255:0] kv_wdata_o,
    output wire [31:0]  kv_wstrb_o,
    // ACTBUF
    output wire [8:0]   act_raddr_o,
    input  wire [63:0]  act_rdata_i,
    output wire         act_we_o,
    output wire [8:0]   act_waddr_o,
    output wire [63:0]  act_wdata_o,
    output wire [7:0]   act_wstrb_o,
    // VECBUF
    output wire [9:0]   vec_raddr_o,
    input  wire [63:0]  vec_rdata_i,
    output wire         vec_we_o,
    output wire [9:0]   vec_waddr_o,
    output wire [63:0]  vec_wdata_o,
    output wire [7:0]   vec_wstrb_o
);

    // ---------------- model constants ----------------
    // llama2.c stories260K: dim=64, hidden=172, 5 layers, 8 q-heads,
    // 4 KV heads (GQA kv_mul=2, kv_dim=32), vocab/context=512.
    localparam [9:0]  SEQ_MAX    = 10'd512;
    localparam [3:0]  ERR_CTX    = 4'd6;

    // ACT word offsets
    localparam [8:0]  AW_X     = 9'd0;
    localparam [8:0]  AW_XB    = 9'd8;
    localparam [8:0]  AW_Q     = 9'd16;
    localparam [8:0]  AW_KT    = 9'd24;
    localparam [8:0]  AW_V     = 9'd32;
    localparam [8:0]  AW_ATT   = 9'd360;
    localparam [8:0]  AW_HB    = 9'd368;
    localparam [8:0]  AW_HB2   = 9'd390;
    localparam [8:0]  AW_HB3   = 9'd412;
    localparam [8:0]  AW_Y     = 9'd434;

    // VEC word offsets
    localparam [9:0]  VW_RQ    = 10'd176;

    // WBUF scale units (16-byte granules)
    localparam [13:0] SU_EMB   = 14'd8224;

    // SFU op codes
    localparam [4:0] OP_EMBED    = 5'd1;
    localparam [4:0] OP_RMSNORM  = 5'd2;
    localparam [4:0] OP_ROPE     = 5'd3;
    localparam [4:0] OP_SWIGLU   = 5'd5;
    localparam [4:0] OP_RESADD   = 5'd6;
    localparam [4:0] OP_KVAPPEND = 5'd7;

    // sequencer states
    localparam [5:0] C_IDLE  = 6'd0;
    localparam [5:0] C_EMB   = 6'd1;
    localparam [5:0] C_RMS1  = 6'd2;
    localparam [5:0] C_QKV   = 6'd3;
    localparam [5:0] C_ROPE  = 6'd4;
    localparam [5:0] C_KVA   = 6'd5;
    localparam [5:0] C_SCORE = 6'd6;
    // Encodings 7/8 are reserved for the removed serial softmax/AV states.
    localparam [5:0] C_WO    = 6'd9;
    localparam [5:0] C_RES1  = 6'd10;
    localparam [5:0] C_RMS2  = 6'd11;
    localparam [5:0] C_W1    = 6'd12;
    localparam [5:0] C_W3    = 6'd13;
    localparam [5:0] C_GLU   = 6'd14;
    localparam [5:0] C_W2    = 6'd15;
    localparam [5:0] C_RES2  = 6'd16;
    localparam [5:0] C_RMSF  = 6'd17;
    localparam [5:0] C_LOG   = 6'd18;
    localparam [5:0] C_TOK   = 6'd19;
    localparam [5:0] C_FIN   = 6'd20;
    localparam [5:0] C_ERR   = 6'd21;

    reg [5:0] state;
    reg       phase;            // 0 = issue, 1 = wait-done
    reg [2:0] layer;
    reg [2:0] head;
    reg [1:0] qkv_i;
    reg [9:0] tok_cnt;
    reg [8:0] token_reg;

    // ---------------- derived base addresses ----------------
    wire [12:0] ltile_w  = 13'd512 + {5'd0, layer} * 13'd720;
    wire [13:0] lsc_u    = SU_EMB + 14'd64 + {6'd0, layer} * 14'd92;
    wire [11:0] lkv_w    = {4'd0, layer} * 12'd768;
    wire [1:0]  kvh      = head[2:1];   // GQA: q head h attends KV head h/2

    // ---------------- SFU instance ----------------
    wire        sfu_start;
    reg  [4:0]  sfu_op;
    reg  [11:0] sfu_p0, sfu_p1;
    reg  [8:0]  sfu_p2;
    wire        sfu_busy, sfu_done;

    wire [8:0]  sfu_act_raddr;
    wire        sfu_act_we;
    wire [8:0]  sfu_act_waddr;
    wire [63:0] sfu_act_wdata;
    wire [7:0]  sfu_act_wstrb;
    wire [9:0]  sfu_vec_raddr;
    wire        sfu_vec_we;
    wire [9:0]  sfu_vec_waddr;
    wire [63:0] sfu_vec_wdata;
    wire [11:0] sfu_kv_raddr;
    wire        sfu_kv_we;
    wire [11:0] sfu_kv_waddr;
    wire [255:0] sfu_kv_wdata;
    wire [31:0] sfu_kv_wstrb;
    wire [12:0] sfu_wbuf_raddr;

    stories260k_sfu u_sfu (
        .clk          (clk),
        .rst_n        (rst_n),
        .soft_reset_i (soft_reset_i),
        .start_i      (sfu_start),
        .op_i         (sfu_op),
        .p0_i         (sfu_p0),
        .p1_i         (sfu_p1),
        .p2_i         (sfu_p2),
        .busy_o       (sfu_busy),
        .done_o       (sfu_done),
        .act_raddr_o  (sfu_act_raddr),
        .act_rdata_i  (act_rdata_i),
        .act_we_o     (sfu_act_we),
        .act_waddr_o  (sfu_act_waddr),
        .act_wdata_o  (sfu_act_wdata),
        .act_wstrb_o  (sfu_act_wstrb),
        .vec_raddr_o  (sfu_vec_raddr),
        .vec_rdata_i  (vec_rdata_i),
        .vec_we_o     (sfu_vec_we),
        .vec_waddr_o  (sfu_vec_waddr),
        .vec_wdata_o  (sfu_vec_wdata),
        .kv_raddr_o   (sfu_kv_raddr),
        .kv_rdata_i   (kv_rdata_i),
        .kv_we_o      (sfu_kv_we),
        .kv_waddr_o   (sfu_kv_waddr),
        .kv_wdata_o   (sfu_kv_wdata),
        .kv_wstrb_o   (sfu_kv_wstrb),
        .wbuf_raddr_o (sfu_wbuf_raddr),
        .wbuf_rdata_i (wbuf_rdata_i)
    );

    // ---------------- fused attention engine ----------------
    wire         attn_start;
    wire         attn_busy;
    wire         attn_done;
    wire [6:0]   attn_mac_adv;
    wire [8:0]   attn_act_raddr;
    wire         attn_act_we;
    wire [8:0]   attn_act_waddr;
    wire [63:0]  attn_act_wdata;
    wire [7:0]   attn_act_wstrb;
    wire [11:0]  attn_kv_raddr;
    wire [11:0]  attn_kv_scale_raddr;

    stories260k_attn u_attn (
        .clk                 (clk),
        .rst_n               (rst_n),
        .soft_reset_i        (soft_reset_i),
        .start_i             (attn_start),
        .pos_i               (seq_pos_o[8:0]),
        .layer_base_i        (lkv_w),
        .kv_head_i           (kvh),
        .q_head_i            (head),
        .sm_shift_i          (cfg_sm_shift_i),
        .busy_o              (attn_busy),
        .done_o              (attn_done),
        .mac_adv_o           (attn_mac_adv),
        .act_raddr_o         (attn_act_raddr),
        .act_rdata_i         (act_rdata_i),
        .act_we_o            (attn_act_we),
        .act_waddr_o         (attn_act_waddr),
        .act_wdata_o         (attn_act_wdata),
        .act_wstrb_o         (attn_act_wstrb),
        .kv_raddr_o          (attn_kv_raddr),
        .kv_rdata_i          (kv_rdata_i),
        .kv_scale_raddr_o    (attn_kv_scale_raddr),
        .kv_scale_rdata_i    (kv_scale_rdata_i)
    );

    // ---------------- MVM engine ----------------
    localparam [2:0] MV_IDLE = 3'd0;
    localparam [2:0] MV_CLR  = 3'd1;
    localparam [2:0] MV_RUN  = 3'd2;
    localparam [2:0] MV_WB   = 3'd3;
    localparam [2:0] MV_DONE = 3'd4;

    reg [2:0]  mv_state;
    wire       mvm_start;
    reg        mv_done;
    wire       mac_clear = (mv_state == MV_CLR);

    // latched MVM configuration
    reg [12:0] cf_wbase;
    reg [1:0]  cf_wsel;      // 0=WBUF tile, 1=KV direct, 2=KV transposed
    reg [13:0] cf_sbase;     // 16-byte units
    reg        cf_scen;
    reg [8:0]  cf_xbase;
    reg [8:0]  cf_ybase;
    reg [1:0]  cf_ymode;     // 0=int8 ACT, 1=raw int32 ACT, 2=argmax
    reg [9:0]  cf_m;
    reg [9:0]  cf_k;
    reg [5:0]  cf_rq;
    reg        cf_i8;
    reg [12:0] cf_i8_base;   // WBUF word base of INT8 high-half tiles

    // sequencer-to-MVM combinational configuration (driven in always @*)
    reg [12:0] mvm_cfg_wbase;
    reg [1:0]  mvm_cfg_wsel;
    reg [13:0] mvm_cfg_sbase;
    reg        mvm_cfg_scen;
    reg [8:0]  mvm_cfg_xbase;
    reg [8:0]  mvm_cfg_ybase;
    reg [1:0]  mvm_cfg_ymode;
    reg [9:0]  mvm_cfg_m;
    reg [9:0]  mvm_cfg_k;
    reg [5:0]  mvm_cfg_rq;
    reg        mvm_cfg_i8;
    reg [12:0] mvm_cfg_i8_base;

    reg [9:0]  mv_mblk;      // current 8-row block
    reg [9:0]  mv_kcnt;      // current 8-element step
    reg [1:0]  mv_gcnt;      // current 64-element scale group
    reg [1:0]  mv_wbsub;     // raw-writeback sub word

    wire [9:0] kwords  = {3'b000, cf_k[9:3]};
    wire [9:0] mblocks = {3'b000, cf_m[9:3]} + {9'd0, |cf_m[2:0]};
    wire [1:0] gpr     = (cf_k[8:6] != 3'd0 && |cf_k[5:0]) ? 2'd3 :
                         (cf_k[8:6] != 3'd0) ? cf_k[7:6] : 2'd1;
    wire [9:0] elem    = mv_kcnt + 10'd1;                  // x8 elements
    wire       grp_last = (mv_state == MV_RUN) &&
                          (({elem, 3'b000} == {3'd0, cf_k}) || (elem[2:0] == 3'd0));

    wire [12:0] mv_waddr = cf_wbase + mv_mblk[9:0] * kwords + {3'd0, mv_kcnt};
    wire [13:0] mv_sunit = cf_sbase + mv_mblk[9:0] * {12'd0, gpr} + {12'd0, mv_gcnt};
    wire [127:0] sc128 = mv_sunit[0] ? wbuf_sdata_i[255:128]
                                     : wbuf_sdata_i[127:0];

    wire [255:0] w_src = (cf_wsel == 2'd2) ? kv_vdata_i :
                         (cf_wsel == 2'd1) ? kv_rdata_i : wbuf_rdata_i;

    // MAC instance
    wire [511:0] w_flat;
    wire [255:0] acc_flat;

    genvar gr, gl;
    generate
        for (gr = 0; gr < 8; gr = gr + 1) begin : g_unpk_row
            for (gl = 0; gl < 8; gl = gl + 1) begin : g_unpk_lane
                if (gr < 4) begin : g_i8_lo
                    assign w_flat[gr*64+gl*8 +: 8] = cf_i8 ?
                        wbuf_rdata_i[gr*64+gl*8 +: 8] :
                        {{4{w_src[gr*32+gl*4+3]}}, w_src[gr*32+gl*4 +: 4]};
                end else begin : g_i8_hi
                    assign w_flat[gr*64+gl*8 +: 8] = cf_i8 ?
                        wbuf_i8_rdata_i[(gr-4)*64+gl*8 +: 8] :
                        {{4{w_src[gr*32+gl*4+3]}}, w_src[gr*32+gl*4 +: 4]};
                end
            end
        end
    endgenerate

    stories260k_mac u_mac (
        .clk          (clk),
        .rst_n        (rst_n),
        .acc_clear_i  (mac_clear),
        .en_i         (mv_state == MV_RUN),
        .grp_last_i   (grp_last),
        .scale_en_i   (cf_scen),
        .w_flat_i     (w_flat),
        .x_flat_i     (act_rdata_i),
        .scale_flat_i (sc128),
        .acc_flat_o   (acc_flat)
    );

    // requant: read slot from VEC rq table
    wire [9:0]  rq_word  = VW_RQ + {4'd0, cf_rq};
    wire [31:0] rq_mult  = vec_rdata_i[31:0];
    wire [7:0]  rq_shift = vec_rdata_i[39:32];

    // argmax tracking
    reg signed [31:0] amax_val;
    reg        [8:0]  amax_idx;

    wire [11:0] cf_m_ext   = {2'b00, cf_m};
    wire [11:0] mblk_rows  = {mv_mblk[8:0], 3'b000};
    wire [11:0] rem_rows   = cf_m_ext - mblk_rows;
    wire [11:0] raw_row0   = mblk_rows + {9'd0, mv_wbsub, 1'b0};

    // per-row writeback results (mode 0)
    integer wr;
    reg signed [31:0] acc_r;
    reg signed [63:0] rq_prod;
    reg signed [63:0] rq_rnd;
    reg signed [63:0] rq_sh;
    reg        [7:0]  y_lane [0:7];

    always @* begin
        for (wr = 0; wr < 8; wr = wr + 1) begin
            acc_r  = acc_flat[wr*32 +: 32];
            rq_prod = acc_r * $signed(rq_mult);
            rq_rnd  = rq_prod +
                      ((rq_shift == 8'd0) ? 64'd0 :
                       ({63'd0, 1'b1} << (rq_shift - 8'd1)));
            rq_sh   = rq_rnd >>> rq_shift;
            y_lane[wr] = (rq_sh > 64'sd127)  ? 8'sd127 :
                         (rq_sh < -64'sd128) ? -8'sd128 : rq_sh[7:0];
        end
    end

    // Decode-time frequency penalty + optional last-K no-repeat (v1.8).
    // Default DEC_CFG: rep_pen=32, adapt_en=0, norep_win=0 → bit-exact R4 golden.
    //   score' = logit - count[token]*pen_eff, count saturates at 15.
    //   pen_eff = adapt_en ? (rep_pen + tok_cnt[9:4]) : rep_pen
    //   norep_win=N bans the last N emitted tokens (hard exclude from argmax).
    reg [3:0] tok_freq [0:511];
    reg [8:0] recent_tok [0:14]; // shift register of last 15 emitted tokens
    reg [3:0] recent_n;          // filled depth (0..15)

    // Effective penalty: base + optional slow ramp with tokens completed.
    wire [8:0] pen_eff = cfg_adapt_en_i
        ? ({1'b0, cfg_rep_pen_i} + {3'd0, tok_cnt[9:4]})
        : {1'b0, cfg_rep_pen_i};

    // Argmax block reduction on *penalized* logits. Ties keep the lowest
    // token index (Python first-maximum rule on the adjusted scores).
    integer ar;
    integer nr;
    reg signed [31:0] blk_best_val;
    reg        [8:0]  blk_best_idx;
    reg               blk_best_en;
    reg signed [31:0] cand_raw;
    reg signed [31:0] cand_adj;
    reg        [8:0]  cand_idx;
    reg               cand_ban;

    always @* begin
        blk_best_val = 32'h8000_0000;
        blk_best_idx = 9'd0;
        blk_best_en  = 1'b0;
        cand_raw     = 32'sd0;
        cand_adj     = 32'sd0;
        cand_idx     = 9'd0;
        cand_ban     = 1'b0;
        for (ar = 0; ar < 8; ar = ar + 1) begin
            cand_idx = {mv_mblk[5:0], ar[2:0]};
            cand_raw = $signed(acc_flat[ar*32 +: 32]);
            cand_adj = cand_raw -
                       ($signed({23'd0, pen_eff}) *
                        $signed({28'd0, tok_freq[cand_idx]}));
            // Hard-ban last-K recent tokens when norep_win != 0.
            cand_ban = 1'b0;
            if (cfg_norep_win_i != 4'd0) begin
                for (nr = 0; nr < 15; nr = nr + 1) begin
                    if ((nr[3:0] < cfg_norep_win_i) && (nr[3:0] < recent_n) &&
                        (cand_idx == recent_tok[nr]))
                        cand_ban = 1'b1;
                end
            end
            if ((ar[11:0] < rem_rows) && !cand_ban &&
                (cand_adj > blk_best_val)) begin
                blk_best_val = cand_adj;
                blk_best_idx = cand_idx;
                blk_best_en  = 1'b1;
            end
        end
    end

    // MVM engine FSM
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mv_state  <= MV_IDLE;
            mv_done   <= 1'b0;
            mv_mblk   <= 10'd0;
            mv_kcnt   <= 10'd0;
            mv_gcnt   <= 2'd0;
            mv_wbsub  <= 2'd0;
            cf_wbase  <= 13'd0;
            cf_wsel   <= 2'd0;
            cf_sbase  <= 14'd0;
            cf_scen   <= 1'b0;
            cf_xbase  <= 9'd0;
            cf_ybase  <= 9'd0;
            cf_ymode  <= 2'd0;
            cf_m      <= 10'd0;
            cf_k      <= 10'd0;
            cf_rq     <= 6'd0;
            cf_i8     <= 1'b0;
            cf_i8_base <= 13'd0;
            amax_val  <= 32'h8000_0000;
            amax_idx  <= 9'd0;
        end else if (soft_reset_i) begin
            mv_state  <= MV_IDLE;
            mv_done   <= 1'b0;
        end else begin
            mv_done   <= 1'b0;
            case (mv_state)
                MV_IDLE: begin
                    mv_wbsub <= 2'd0;
                    if (mvm_start) begin
                        cf_wbase <= mvm_cfg_wbase;
                        cf_wsel  <= mvm_cfg_wsel;
                        cf_sbase <= mvm_cfg_sbase;
                        cf_scen  <= mvm_cfg_scen;
                        cf_xbase <= mvm_cfg_xbase;
                        cf_ybase <= mvm_cfg_ybase;
                        cf_ymode <= mvm_cfg_ymode;
                        cf_m     <= mvm_cfg_m;
                        cf_k     <= mvm_cfg_k;
                        cf_rq    <= mvm_cfg_rq;
                        cf_i8    <= mvm_cfg_i8;
                        cf_i8_base <= mvm_cfg_i8_base;
                        mv_mblk  <= 10'd0;
                        mv_kcnt  <= 10'd0;
                        mv_gcnt  <= 2'd0;
                        if (mvm_cfg_ymode == 2'd2) begin
                            amax_val <= 32'h8000_0000;
                            amax_idx <= 9'd0;
                        end
                        mv_state  <= MV_CLR;
                    end
                end
                MV_CLR: begin
                    mv_state <= MV_RUN;
                end
                MV_RUN: begin
                    mv_gcnt <= mv_gcnt + {1'b0, grp_last};
                    if (mv_kcnt == kwords - 10'd1) begin
                        mv_kcnt  <= 10'd0;
                        mv_gcnt  <= 2'd0;
                        mv_wbsub <= 2'd0;
                        mv_state <= MV_WB;
                    end else begin
                        mv_kcnt <= mv_kcnt + 10'd1;
                    end
                end
                MV_WB: begin
                    if (cf_ymode == 2'd1 && mv_wbsub != 2'd3) begin
                        mv_wbsub <= mv_wbsub + 2'd1;
                    end else begin
                        if (cf_ymode == 2'd2 && blk_best_en &&
                            blk_best_val > amax_val) begin
                            amax_val <= blk_best_val;
                            amax_idx <= blk_best_idx;
                        end
                        if (mv_mblk == mblocks - 10'd1) begin
                            mv_state <= MV_DONE;
                        end else begin
                            mv_mblk   <= mv_mblk + 10'd1;
                            mv_state  <= MV_CLR;
                        end
                    end
                end
                MV_DONE: begin
                    mv_done  <= 1'b1;
                    mv_state <= MV_IDLE;
                end
                default: mv_state <= MV_IDLE;
            endcase
        end
    end

    // ---------------- SPM port mux (SFU, then attention, then MVM) ----------------
    wire mvm_act_we = (mv_state == MV_WB) && (cf_ymode != 2'd2);

    wire [8:0] mvm_act_waddr = (cf_ymode == 2'd1) ?
        (cf_ybase + {mv_mblk[6:0], 2'b00} + {7'd0, mv_wbsub}) :
        (cf_ybase + mv_mblk[8:0]);

    wire [63:0] mvm_act_wdata = (cf_ymode == 2'd1) ?
        {acc_flat[{mv_wbsub, 1'b1}*32 +: 32], acc_flat[{mv_wbsub, 1'b0}*32 +: 32]} :
        {y_lane[7], y_lane[6], y_lane[5], y_lane[4],
         y_lane[3], y_lane[2], y_lane[1], y_lane[0]};

    wire [7:0] mvm_act_wstrb;
    assign mvm_act_wstrb =
        (cf_ymode == 2'd1) ?
            ((raw_row0 + 12'd1 < cf_m_ext) ? 8'hFF :
             (raw_row0 < cf_m_ext)           ? 8'h0F : 8'h00) :
            ((rem_rows >= 12'd8) ? 8'hFF : (8'hFF >> (4'd8 - rem_rows[3:0])));

    assign act_raddr_o = sfu_busy ? sfu_act_raddr :
                             attn_busy ? attn_act_raddr : (cf_xbase + mv_kcnt[8:0]);
    assign act_we_o    = sfu_busy ? sfu_act_we :
                             attn_busy ? attn_act_we : mvm_act_we;
    assign act_waddr_o = sfu_busy ? sfu_act_waddr :
                             attn_busy ? attn_act_waddr : mvm_act_waddr;
    assign act_wdata_o = sfu_busy ? sfu_act_wdata :
                             attn_busy ? attn_act_wdata : mvm_act_wdata;
    assign act_wstrb_o = sfu_busy ? sfu_act_wstrb :
                             attn_busy ? attn_act_wstrb : mvm_act_wstrb;

    assign vec_raddr_o = sfu_busy ? sfu_vec_raddr : rq_word;
    assign vec_we_o    = sfu_vec_we;
    assign vec_waddr_o = sfu_vec_waddr;
    assign vec_wdata_o = sfu_vec_wdata;

    assign kv_raddr_o  = sfu_busy ? sfu_kv_raddr :
                             attn_busy ? attn_kv_raddr : mv_waddr[11:0];
    assign kv_scale_raddr_o = attn_kv_scale_raddr;
    assign kv_we_o     = sfu_kv_we;
    assign kv_waddr_o  = sfu_kv_waddr;
    assign kv_wdata_o  = sfu_kv_wdata;
    assign kv_wstrb_o  = sfu_kv_wstrb;

    assign wbuf_raddr_o = sfu_busy ? sfu_wbuf_raddr : mv_waddr;
    assign wbuf_saddr_o = mv_sunit[13:1];
    // INT8 high-half tile bank: base selected per matrix (see C_QKV).
    assign wbuf_i8_raddr_o = cf_i8 ?
        (cf_i8_base + mv_mblk[9:0] * kwords + {3'd0, mv_kcnt}) : 13'd0;

    // SFU always writes full 64-bit VEC words
    assign vec_wstrb_o = 8'hFF;

    assign mac_adv_o = attn_busy ? attn_mac_adv :
                       ((mv_state == MV_RUN) ? 7'd64 : 7'd0);

    // ---------------- sequencer: combinational per-state config ----------------
    wire [5:0] rq_layer = {3'd0, layer} * 3'd7;

    wire is_sfu = (state == C_EMB)  || (state == C_RMS1) || (state == C_ROPE) ||
                  (state == C_KVA)  || (state == C_RES1) ||
                  (state == C_RMS2) || (state == C_GLU)  || (state == C_RES2) ||
                  (state == C_RMSF);
    wire is_mvm = (state == C_QKV) || (state == C_WO) ||
                  (state == C_W1)  || (state == C_W3) ||
                  (state == C_W2)  || (state == C_LOG);
    wire is_attn = (state == C_SCORE);

    always @* begin
        sfu_op = 5'd0;
        sfu_p0 = 12'd0;
        sfu_p1 = 12'd0;
        sfu_p2 = 9'd0;
        mvm_cfg_wbase = 13'd0;
        mvm_cfg_wsel  = 2'd0;
        mvm_cfg_sbase = 14'd0;
        mvm_cfg_scen  = 1'b0;
        mvm_cfg_xbase = 9'd0;
        mvm_cfg_ybase = 9'd0;
        mvm_cfg_ymode = 2'd0;
        mvm_cfg_m     = 10'd0;
        mvm_cfg_k     = 10'd0;
        mvm_cfg_rq    = 6'd0;
        mvm_cfg_i8    = 1'b0;
        mvm_cfg_i8_base = 13'd0;
        case (state)
            C_EMB: begin
                sfu_op = OP_EMBED;
                sfu_p0 = {3'd0, token_reg};
            end
            C_RMS1: begin
                sfu_op = OP_RMSNORM;
                sfu_p0 = {3'd0, AW_X};
                sfu_p1 = {4'd0, layer, 5'b00000};
                sfu_p2 = AW_XB;
            end
            C_ROPE: begin
                sfu_op = OP_ROPE;
                sfu_p0 = {3'd0, seq_pos_o[8:0]};
                sfu_p1 = {3'd0, AW_Q};
                sfu_p2 = AW_KT;
            end
            C_KVA: begin
                sfu_op = OP_KVAPPEND;
                sfu_p0 = {3'd0, seq_pos_o[8:0]};
                sfu_p1 = lkv_w;
            end
            C_RES1, C_RES2: begin
                sfu_op = OP_RESADD;
                sfu_p0 = {3'd0, AW_X};
                sfu_p1 = {3'd0, AW_Y};
            end
            C_RMS2: begin
                sfu_op = OP_RMSNORM;
                sfu_p0 = {3'd0, AW_X};
                sfu_p1 = {4'd0, layer, 5'b00000} + 12'd16;
                sfu_p2 = AW_XB;
            end
            C_GLU: begin
                sfu_op = OP_SWIGLU;
                sfu_p0 = {3'd0, AW_HB};
                sfu_p1 = {3'd0, AW_HB2};
                sfu_p2 = AW_HB3;
            end
            C_RMSF: begin
                sfu_op = OP_RMSNORM;
                sfu_p0 = {3'd0, AW_X};
                sfu_p1 = 12'd160;
                sfu_p2 = AW_XB;
            end
            C_QKV: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = ltile_w + ((qkv_i == 2'd0) ? 13'd0 :
                                (qkv_i == 2'd1) ? 13'd64 : 13'd96);
                mvm_cfg_sbase = lsc_u + ((qkv_i == 2'd0) ? 14'd0 :
                                (qkv_i == 2'd1) ? 14'd8 : 14'd12);
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_XB;
                mvm_cfg_ybase = (qkv_i == 2'd0) ? AW_Q :
                                (qkv_i == 2'd1) ? AW_KT : AW_V;
                mvm_cfg_ymode = 2'd0;
                mvm_cfg_m     = (qkv_i == 2'd0) ? 10'd64 : 10'd32;
                mvm_cfg_k     = 10'd64;
                mvm_cfg_rq    = rq_layer + {4'd0, qkv_i};
                // Design-B v1.7 INT8 high-halves (low 4 rows in normal tiles):
                //   L1 WQ 4630..4693 (64), WK 4694..4725 (32), WV 4726..4757 (32)
                //   L2 WQ 4822..4885 (64), L3 WQ 4950..5013 (64)
                mvm_cfg_i8 = (layer == 3'd1) ||
                             ((layer == 3'd2) && (qkv_i == 2'd0)) ||
                             ((layer == 3'd3) && (qkv_i == 2'd0));
                mvm_cfg_i8_base = (layer == 3'd1) ?
                                  ((qkv_i == 2'd0) ? 13'd4630 :
                                   (qkv_i == 2'd1) ? 13'd4694 : 13'd4726) :
                                  (layer == 3'd2) ? 13'd4822 : 13'd4950;
            end
            C_WO: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = ltile_w + 13'd128;
                mvm_cfg_sbase = lsc_u + 14'd16;
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_ATT;
                mvm_cfg_ybase = AW_Y;
                mvm_cfg_ymode = 2'd0;
                mvm_cfg_m     = 10'd64;
                mvm_cfg_k     = 10'd64;
                mvm_cfg_rq    = rq_layer + 6'd3;
                // L1 WO 4758..4821, L2 WO 4886..4949 (64 words each)
                mvm_cfg_i8 = (layer == 3'd1) || (layer == 3'd2);
                mvm_cfg_i8_base = (layer == 3'd1) ? 13'd4758 : 13'd4886;
            end
            C_W1: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = ltile_w + 13'd192;
                mvm_cfg_sbase = lsc_u + 14'd24;
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_XB;
                mvm_cfg_ybase = AW_HB;
                mvm_cfg_ymode = 2'd0;
                mvm_cfg_m     = 10'd172;
                mvm_cfg_k     = 10'd64;
                mvm_cfg_rq    = rq_layer + 6'd4;
            end
            C_W3: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = ltile_w + 13'd544;
                mvm_cfg_sbase = lsc_u + 14'd70;
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_XB;
                mvm_cfg_ybase = AW_HB2;
                mvm_cfg_ymode = 2'd0;
                mvm_cfg_m     = 10'd172;
                mvm_cfg_k     = 10'd64;
                mvm_cfg_rq    = rq_layer + 6'd6;
            end
            C_W2: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = ltile_w + 13'd368;
                mvm_cfg_sbase = lsc_u + 14'd46;
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_HB3;
                mvm_cfg_ybase = AW_Y;
                mvm_cfg_ymode = 2'd0;
                mvm_cfg_m     = 10'd64;
                mvm_cfg_k     = 10'd176;
                mvm_cfg_rq    = rq_layer + 6'd5;
            end
            C_LOG: begin
                mvm_cfg_wsel  = 2'd0;
                mvm_cfg_wbase = 13'd0;
                mvm_cfg_sbase = SU_EMB;
                mvm_cfg_scen  = 1'b1;
                mvm_cfg_xbase = AW_XB;
                mvm_cfg_ybase = 9'd0;
                mvm_cfg_ymode = 2'd2;
                mvm_cfg_m     = 10'd512;
                mvm_cfg_k     = 10'd64;
                mvm_cfg_rq    = 6'd0;
            end
            default: ;
        endcase
    end

    assign sfu_start  = is_sfu  && (phase == 1'b0) && (state != C_IDLE);
    assign mvm_start  = is_mvm  && (phase == 1'b0);
    assign attn_start = is_attn && (phase == 1'b0);

    wire unit_done = sfu_done | mv_done | attn_done;

    // ---------------- sequencer: clocked FSM ----------------
    assign busy_o     = (state != C_IDLE);
    assign cycle_en_o = busy_o;

    integer fi;
    integer ri;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state             <= C_IDLE;
            phase             <= 1'b0;
            layer             <= 3'd0;
            head              <= 3'd0;
            qkv_i             <= 2'd0;
            tok_cnt           <= 10'd0;
            token_reg         <= 9'd0;
            seq_pos_o         <= 10'd0;
            token_out_o       <= 9'd0;
            done_set_o        <= 1'b0;
            error_set_o       <= 1'b0;
            error_code_o      <= 4'd0;
            token_valid_set_o <= 1'b0;
            token_inc_o       <= 1'b0;
            recent_n          <= 4'd0;
            for (fi = 0; fi < 512; fi = fi + 1)
                tok_freq[fi] <= 4'd0;
            for (ri = 0; ri < 15; ri = ri + 1)
                recent_tok[ri] <= 9'd0;
        end else if (soft_reset_i) begin
            state             <= C_IDLE;
            phase             <= 1'b0;
            layer             <= 3'd0;
            head              <= 3'd0;
            qkv_i             <= 2'd0;
            tok_cnt           <= 10'd0;
            token_reg         <= 9'd0;
            seq_pos_o         <= 10'd0;
            token_out_o       <= 9'd0;
            done_set_o        <= 1'b0;
            error_set_o       <= 1'b0;
            error_code_o      <= 4'd0;
            token_valid_set_o <= 1'b0;
            token_inc_o       <= 1'b0;
            recent_n          <= 4'd0;
            for (fi = 0; fi < 512; fi = fi + 1)
                tok_freq[fi] <= 4'd0;
            for (ri = 0; ri < 15; ri = ri + 1)
                recent_tok[ri] <= 9'd0;
        end else begin
            done_set_o        <= 1'b0;
            error_set_o       <= 1'b0;
            token_valid_set_o <= 1'b0;
            token_inc_o       <= 1'b0;

            case (state)
                C_IDLE: begin
                    if (start_pulse_i) begin
                        token_reg <= cfg_token_in_i;
                        seq_pos_o <= 10'd0;
                        tok_cnt   <= 10'd0;
                        layer     <= 3'd0;
                        head      <= 3'd0;
                        qkv_i     <= 2'd0;
                        phase     <= 1'b0;
                        state     <= C_EMB;
                        // Fresh decode context: clear frequency / norep state.
                        recent_n  <= 4'd0;
                        for (fi = 0; fi < 512; fi = fi + 1)
                            tok_freq[fi] <= 4'd0;
                        for (ri = 0; ri < 15; ri = ri + 1)
                            recent_tok[ri] <= 9'd0;
                    end
                end

                C_TOK: begin
                    token_out_o       <= amax_idx;
                    token_reg         <= amax_idx;
                    token_valid_set_o <= 1'b1;
                    token_inc_o       <= 1'b1;
                    seq_pos_o         <= seq_pos_o + 10'd1;
                    tok_cnt           <= tok_cnt + 10'd1;
                    // Saturating frequency counter for the chosen token.
                    if (tok_freq[amax_idx] != 4'd15)
                        tok_freq[amax_idx] <= tok_freq[amax_idx] + 4'd1;
                    // Shift recent history: newest at index 0.
                    for (ri = 14; ri > 0; ri = ri - 1)
                        recent_tok[ri] <= recent_tok[ri - 1];
                    recent_tok[0] <= amax_idx;
                    if (recent_n != 4'd15)
                        recent_n <= recent_n + 4'd1;
                    if (cfg_chain_en_i && (tok_cnt[8:0] != cfg_gen_len_i)) begin
                        if (seq_pos_o == SEQ_MAX - 10'd1) begin
                            error_code_o <= ERR_CTX;
                            state        <= C_ERR;
                        end else begin
                            state <= C_EMB;
                        end
                    end else begin
                        state <= C_FIN;
                    end
                end

                C_FIN: begin
                    done_set_o <= 1'b1;
                    state      <= C_IDLE;
                end

                C_ERR: begin
                    error_set_o <= 1'b1;
                    state       <= C_IDLE;
                end

                default: begin
                    if (phase == 1'b0) begin
                        phase <= 1'b1;
                    end else if (unit_done) begin
                        phase <= 1'b0;
                        case (state)
                            C_EMB:   state <= C_RMS1;
                            C_RMS1:  state <= C_QKV;
                            C_QKV: begin
                                if (qkv_i == 2'd2) begin
                                    qkv_i <= 2'd0;
                                    state <= C_ROPE;
                                end else begin
                                    qkv_i <= qkv_i + 2'd1;
                                end
                            end
                            C_ROPE:  state <= C_KVA;
                            C_KVA:   state <= C_SCORE;
                            C_SCORE: begin
                                if (head == 3'd7) begin
                                    head  <= 3'd0;
                                    state <= C_WO;
                                end else begin
                                    head  <= head + 3'd1;
                                    state <= C_SCORE;
                                end
                            end
                            C_WO:    state <= C_RES1;
                            C_RES1:  state <= C_RMS2;
                            C_RMS2:  state <= C_W1;
                            C_W1:    state <= C_W3;
                            C_W3:    state <= C_GLU;
                            C_GLU:   state <= C_W2;
                            C_W2:    state <= C_RES2;
                            C_RES2: begin
                                if (layer == 3'd4) begin
                                    layer <= 3'd0;
                                    state <= C_RMSF;
                                end else begin
                                    layer <= layer + 3'd1;
                                    state <= C_RMS1;
                                end
                            end
                            C_RMSF:  state <= C_LOG;
                            C_LOG:   state <= C_TOK;
                            default: state <= C_IDLE;
                        endcase
                    end
                end
            endcase
        end
    end

endmodule
