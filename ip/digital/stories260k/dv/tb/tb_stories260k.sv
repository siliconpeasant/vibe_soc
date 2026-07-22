//============================================================================
// Testbench  : tb_stories260k
// Function   : PoC verification for the stories260k inference engine
//
//   T1  ID/VERSION register check
//   T2  stories260k_mac directed test vs SV golden model (fused dequant)
//   T3  512-position layout boundaries plus chained-token decode;
//        default: 64 tokens, two-run determinism, throughput >= 8700 tok/s
//        TESTNAME=long512: one real-image 512-token context-boundary run
//   T4  MMIO invalid-address error injection
//
// Optional plusargs:
//   +WIMAGE=<hex>  $readmemh image for WBUF (real stories260K quantization)
//   +VIMAGE=<hex>  $readmemh image for VECBUF (gains/requant tables)
//   +TESTNAME=long512  generate the full 512-token checkpoint context
//   +SEED_TOKEN=<id>   TOKEN_IN seed (default 1 = BOS). Non-BOS skips fixed
//                      golden match so alternate stories can be explored.
//   +DEC_PROFILE=golden|mid|long  decode policy preset (overridden by fields)
//   +REP_PEN=<0..255>  DEC_CFG.rep_pen (default 32 = R4 golden)
//   +ADAPT_EN=<0|1>    DEC_CFG.adapt_en (default 0)
//   +NOREP_WIN=<0..15> DEC_CFG.norep_win last-K ban (default 0)
//   Non-default DEC_CFG disables the 64-token fixed-model golden check.
// Without images, deterministic LFSR pseudo-random weights are loaded.
//============================================================================

`timescale 1ns/1ps

module tb_stories260k #(
    parameter integer DEFAULT_GEN_TOKENS = 64,
    parameter integer DEFAULT_LONG_MODE  = 0,
    parameter integer DEFAULT_TRACE_NUM  = 0
);

    localparam [19:0] CSR_BASE  = 20'h00000;
    localparam [19:0] WBUF_BASE = 20'h10000;
    localparam [19:0] VEC_BASE  = 20'h64000;

    localparam [11:0] REG_ID       = 12'h000;
    localparam [11:0] REG_VERSION  = 12'h004;
    localparam [11:0] REG_CTRL     = 12'h008;
    localparam [11:0] REG_STATUS   = 12'h00C;
    localparam [11:0] REG_TOKEN_IN = 12'h010;
    localparam [11:0] REG_TOKEN_O  = 12'h014;
    localparam [11:0] REG_SEQ_POS  = 12'h018;
    localparam [11:0] REG_GEN_CFG  = 12'h01C;
    localparam [11:0] REG_CYCLE_LO = 12'h020;
    localparam [11:0] REG_CYCLE_HI = 12'h024;
    localparam [11:0] REG_TOKEN_CT = 12'h028;
    localparam [11:0] REG_MAC_LO   = 12'h02C;
    localparam [11:0] REG_MAC_HI   = 12'h030;
    localparam [11:0] REG_PERF_CLR = 12'h034;
    localparam [11:0] REG_DEC_CFG  = 12'h038; // rep_pen/adapt/norep; leave at reset

    localparam integer MAX_GEN_TOKENS = 512;
    localparam integer WGT_BYTES    = 131584;   // baseline tiled INT4 weights
    localparam integer SC_BYTES     = 8384;     // group scales
    localparam integer WBUF_BYTES   = WGT_BYTES + SC_BYTES;
    localparam integer WBUF_ROPE_W  = 4374;
    localparam integer GAIN_WORDS_B = 1408;     // 11 x 64 x int16
    localparam integer ROPE_POS     = 512;
    localparam integer RQ_W         = 176;
    localparam integer RQ_SLOTS     = 37;
    localparam integer SM_SHIFT     = 1;   // calibrated for QAT mixed-W4/W8 (v1.3)
    localparam integer WBUF_LAST_W  = 5013;     // layer-3 WQ INT8 high halves (v1.7)
    localparam integer WBUF_CAP_W   = 5024;     // WBUF_WORDS in stories260k_spm
    localparam integer KV_LAST_W    = 3839;
    localparam integer ACT_LAST_W   = 441;
    localparam integer VEC_LAST_W   = 212;

    reg         clk;
    reg         rst_n;
    reg         mm_valid;
    reg         mm_write;
    reg  [19:0] mm_addr;
    reg  [31:0] mm_wdata;
    reg  [3:0]  mm_wstrb;
    wire [31:0] mm_rdata;
    wire        mm_ready;
    wire        mm_error;
    wire        irq;

    integer errors;
    integer tok_seen;
    integer gen_tokens;
    integer wait_limit;
    integer seed_tmp;
    integer rep_pen_i;
    integer adapt_en_i;
    integer norep_win_i;
    reg     long_mode;
    reg [8:0] seed_token;
    reg       check_golden;
    reg [7:0] rep_pen;
    reg       adapt_en;
    reg [3:0] norep_win;
    string  test_name;
    string  dec_profile;
    reg     capture_enable;
    reg [8:0]   tok_run1 [0:MAX_GEN_TOKENS-1];
    reg [8:0]   tok_run2 [0:MAX_GEN_TOKENS-1];

    // ------------------------------------------------------------------
    // DUT
    // ------------------------------------------------------------------
    stories260k u_dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .mm_valid (mm_valid),
        .mm_write (mm_write),
        .mm_addr  (mm_addr),
        .mm_wdata (mm_wdata),
        .mm_wstrb (mm_wstrb),
        .mm_rdata (mm_rdata),
        .mm_ready (mm_ready),
        .mm_error (mm_error),
        .irq      (irq)
    );

    // ------------------------------------------------------------------
    // MAC unit-level DUT (T2)
    // ------------------------------------------------------------------
    reg         mac_clk_en;
    reg         mac_clear;
    reg         mac_grp_last;
    reg         mac_scale_en;
    reg  [511:0] mac_w;
    reg  [63:0]  mac_x;
    reg  [127:0] mac_scale;
    wire [255:0] mac_acc;

    stories260k_mac u_mac_dut (
        .clk          (clk),
        .rst_n        (rst_n),
        .acc_clear_i  (mac_clear),
        .en_i         (mac_clk_en),
        .grp_last_i   (mac_grp_last),
        .scale_en_i   (mac_scale_en),
        .w_flat_i     (mac_w),
        .x_flat_i     (mac_x),
        .scale_flat_i (mac_scale),
        .acc_flat_o   (mac_acc)
    );

    // ------------------------------------------------------------------
    // Clock / reset
    // ------------------------------------------------------------------
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------
    reg [31:0] lfsr;

    function [31:0] xorshift;
        input [31:0] s;
        reg [31:0] v;
        begin
            v = s;
            v = v ^ (v << 13);
            v = v ^ (v >> 17);
            v = v ^ (v << 5);
            xorshift = v;
        end
    endfunction

    // Fixed-point golden trajectory for the real mixed W4/W8 checkpoint
    // image.  This prefix is long enough to cross every transformer layer
    // repeatedly and catches arithmetic/layout drift that legality and
    // determinism checks alone cannot detect.
    function [8:0] golden_token;
        input integer idx;
        begin
            case (idx)
                 0: golden_token = 9'd403;   1: golden_token = 9'd407;
                 2: golden_token = 9'd261;   3: golden_token = 9'd378;
                 4: golden_token = 9'd432;   5: golden_token = 9'd383;
                 6: golden_token = 9'd286;   7: golden_token = 9'd261;
                 8: golden_token = 9'd376;   9: golden_token = 9'd298;
                10: golden_token = 9'd315;  11: golden_token = 9'd421;
                12: golden_token = 9'd395;  13: golden_token = 9'd317;
                14: golden_token = 9'd426;  15: golden_token = 9'd338;
                16: golden_token = 9'd401;  17: golden_token = 9'd396;
                18: golden_token = 9'd267;  19: golden_token = 9'd337;
                20: golden_token = 9'd335;  21: golden_token = 9'd311;
                22: golden_token = 9'd267;  23: golden_token = 9'd422;
                24: golden_token = 9'd419;  25: golden_token = 9'd269;
                26: golden_token = 9'd279;  27: golden_token = 9'd303;
                28: golden_token = 9'd331;  29: golden_token = 9'd426;
                30: golden_token = 9'd385;  31: golden_token = 9'd328;
                32: golden_token = 9'd432;  33: golden_token = 9'd358;
                34: golden_token = 9'd394;  35: golden_token = 9'd261;
                36: golden_token = 9'd370;  37: golden_token = 9'd268;
                38: golden_token = 9'd388;  39: golden_token = 9'd426;
                40: golden_token = 9'd338;  41: golden_token = 9'd381;
                42: golden_token = 9'd261;  43: golden_token = 9'd416;
                44: golden_token = 9'd410;  45: golden_token = 9'd449;
                46: golden_token = 9'd425;  47: golden_token = 9'd417;
                48: golden_token = 9'd331;  49: golden_token = 9'd286;
                50: golden_token = 9'd399;  51: golden_token = 9'd393;
                52: golden_token = 9'd426;  53: golden_token = 9'd13;
                54: golden_token = 9'd441;  55: golden_token = 9'd416;
                56: golden_token = 9'd411;  57: golden_token = 9'd328;
                58: golden_token = 9'd432;  59: golden_token = 9'd358;
                60: golden_token = 9'd272;  61: golden_token = 9'd277;
                62: golden_token = 9'd264;  63: golden_token = 9'd261;
                default: golden_token = 9'd0;
            endcase
        end
    endfunction

    task mm_wr;
        input [19:0] a;
        input [31:0] d;
        begin
            @(posedge clk);
            mm_valid <= 1'b1;
            mm_write <= 1'b1;
            mm_addr  <= a;
            mm_wdata <= d;
            mm_wstrb <= 4'hF;
            @(posedge clk);
            mm_valid <= 1'b0;
            mm_write <= 1'b0;
        end
    endtask

    task mm_rd;
        input  [19:0] a;
        output [31:0] d;
        output        e;
        begin
            @(posedge clk);
            mm_valid <= 1'b1;
            mm_write <= 1'b0;
            mm_addr  <= a;
            mm_wstrb <= 4'h0;
            @(posedge clk);
            mm_valid <= 1'b0;
            // mm_rdata/mm_error are registered at the t1 edge and held until
            // the t2 edge NBA update; sampling in the t2 active region is
            // race-free.
            @(posedge clk);
            d = mm_rdata;
            e = mm_error;
        end
    endtask

    task fail;
        input [8*80-1:0] msg;
        begin
            errors = errors + 1;
            $display("[%0t] FAIL: %0s", $time, msg);
        end
    endtask

    // ------------------------------------------------------------------
    // Image loading
    // ------------------------------------------------------------------
    reg [1023:0] wimage, vimage;
    integer      have_wimage, have_vimage;
    integer      i, j, p;
    reg [31:0]   rd;
    reg          rerr;
    real         fr, cr, sr;
    integer      cval [0:3];
    integer      sval [0:3];

    task load_wbuf_lfsr;
        begin
            lfsr = 32'h260C_0ACE;
            for (i = 0; i < WBUF_BYTES/4; i = i + 1) begin
                if (i < WGT_BYTES/4) begin
                    lfsr = xorshift(lfsr);
                    rd   = lfsr;
                end else begin
                    rd = 32'h0800_0800;  // group scale 0.5 (Q4.12)
                end
                mm_wr(WBUF_BASE + i*4, rd);
            end
        end
    endtask

    task load_vecbuf;
        begin
            // RMSNorm gains = 1.0 (Q2.14)
            for (i = 0; i < GAIN_WORDS_B/4; i = i + 1)
                mm_wr(VEC_BASE + i*4, 32'h4000_4000);
            // RoPE table in WBUF spare: each position is cos64 then sin64.
            for (p = 0; p < ROPE_POS; p = p + 1) begin
                for (j = 0; j < 4; j = j + 1) begin
                    fr = p * (10000.0 ** (-2.0*j/8.0));
                    cr = $cos(fr);
                    sr = $sin(fr);
                    cval[j] = $rtoi(cr * 16384.0 + (cr >= 0.0 ? 0.5 : -0.5));
                    sval[j] = $rtoi(sr * 16384.0 + (sr >= 0.0 ? 0.5 : -0.5));
                end
                mm_wr(WBUF_BASE + WBUF_ROPE_W*32 + p*16,
                      {cval[1][15:0], cval[0][15:0]});
                mm_wr(WBUF_BASE + WBUF_ROPE_W*32 + p*16 + 4,
                      {cval[3][15:0], cval[2][15:0]});
                mm_wr(WBUF_BASE + WBUF_ROPE_W*32 + p*16 + 8,
                      {sval[1][15:0], sval[0][15:0]});
                mm_wr(WBUF_BASE + WBUF_ROPE_W*32 + p*16 + 12,
                      {sval[3][15:0], sval[2][15:0]});
            end
            // requant table: mult=1, shift=8
            for (i = 0; i < RQ_SLOTS; i = i + 1) begin
                mm_wr(VEC_BASE + RQ_W*8 + i*8,     32'd1);
                mm_wr(VEC_BASE + RQ_W*8 + i*8 + 4, 32'd8);
            end
        end
    endtask

    task check_rope_pos;
        input integer pos;
        integer wi;
        reg [63:0] exp_cos, exp_sin;
        reg [63:0] got_cos, got_sin;
        reg [255:0] rope_word;
        begin
            for (j = 0; j < 4; j = j + 1) begin
                fr = pos * (10000.0 ** (-2.0*j/8.0));
                cr = $cos(fr);
                sr = $sin(fr);
                cval[j] = $rtoi(cr * 16384.0 + (cr >= 0.0 ? 0.5 : -0.5));
                sval[j] = $rtoi(sr * 16384.0 + (sr >= 0.0 ? 0.5 : -0.5));
            end
            exp_cos = {cval[3][15:0], cval[2][15:0],
                       cval[1][15:0], cval[0][15:0]};
            exp_sin = {sval[3][15:0], sval[2][15:0],
                       sval[1][15:0], sval[0][15:0]};
            wi = WBUF_ROPE_W + (pos >> 1);
            rope_word = u_dut.u_spm.wbuf_mem[wi];
            if ((pos & 1) == 0) begin
                got_cos = rope_word[63:0];
                got_sin = rope_word[127:64];
            end else begin
                got_cos = rope_word[191:128];
                got_sin = rope_word[255:192];
            end
            if (got_cos !== exp_cos || got_sin !== exp_sin) begin
                errors = errors + 1;
                $display("[%0t] FAIL: RoPE table pos=%0d cos=%h/%h sin=%h/%h",
                         $time, pos, got_cos, exp_cos, got_sin, exp_sin);
            end
        end
    endtask

    // ------------------------------------------------------------------
    // T2: MAC golden model
    // ------------------------------------------------------------------
    integer g_acc [0:7];
    integer g_part [0:7];

    task mac_golden_clear;
        integer r;
        begin
            for (r = 0; r < 8; r = r + 1) begin
                g_acc[r]  = 0;
                g_part[r] = 0;
            end
        end
    endtask

    task mac_golden_step;
        input glast;
        integer r, l;
        integer d, s;
        integer wx, xx;
        longint prod;
        begin
            for (r = 0; r < 8; r = r + 1) begin
                d = 0;
                for (l = 0; l < 8; l = l + 1) begin
                    wx = $signed(mac_w[r*64+l*8 +: 8]);
                    xx = $signed(mac_x[l*8 +: 8]);
                    d  = d + wx*xx;
                end
                s = mac_scale_en ? $signed(mac_scale[r*16 +: 16]) : 4096;
                if (glast) begin
                    // RTL: (part + dot) * scale + 2048 >>> 12 (round-half-up)
                    prod      = (g_part[r] + d);
                    prod      = (prod * s + 2048) >>> 12;
                    g_acc[r]  = g_acc[r] + prod[31:0];
                    g_part[r] = 0;
                end else begin
                    g_part[r] = g_part[r] + d;
                end
            end
        end
    endtask

    task mac_check_acc;
        integer r;
        integer hw;
        begin
            for (r = 0; r < 8; r = r + 1) begin
                hw = $signed(mac_acc[r*32 +: 32]);
                if (hw !== g_acc[r]) begin
                    errors = errors + 1;
                    $display("[%0t] FAIL: MAC row %0d acc=%0d golden=%0d",
                             $time, r, hw, g_acc[r]);
                end
            end
        end
    endtask

    task mac_random_trial;
        input integer steps;
        input integer s_en;
        integer t, b;
        begin
            mac_golden_clear;
            @(posedge clk);
            mac_clear   <= 1'b1;
            mac_clk_en  <= 1'b0;
            mac_scale_en <= s_en;
            @(posedge clk);
            mac_clear <= 1'b0;
            for (t = 0; t < steps; t = t + 1) begin
                lfsr = xorshift(lfsr);
                mac_w = {lfsr, xorshift(lfsr), xorshift(xorshift(lfsr)),
                         32'hA5A5_5A5A, 32'h1357_9BDF, 32'h2468_ACEF,
                         32'h0F0F_F0F0, 32'hDEAD_BEEF, 32'h1234_5678,
                         32'hCAFE_F00D, 32'h55AA_55AA, 32'h33CC_33CC,
                         32'h7777_1111, 32'h0ACE_260C, 32'hFEDC_BA98,
                         32'h8642_7531};
                mac_x = {xorshift(lfsr ^ 32'h5EED_CAFE), xorshift(lfsr)};
                for (b = 0; b < 8; b = b + 1) begin
                    lfsr = xorshift(lfsr);
                    mac_scale[b*16 +: 16] = lfsr[15:0];
                end
                mac_clk_en  <= 1'b1;
                mac_grp_last <= (t == steps-1);
                mac_golden_step(t == steps-1);
                @(posedge clk);
            end
            mac_clk_en  <= 1'b0;
            mac_grp_last <= 1'b0;
            // let the last accumulate edge settle before reading acc
            @(posedge clk);
            mac_check_acc;
        end
    endtask

    // ------------------------------------------------------------------
    // Token capture (hierarchical observability)
    // ------------------------------------------------------------------
    integer run_phase;

    // optional debug: dump x after EMBED and xb after first RMSNORM
    reg dbg_x_done, dbg_xb_done;
    initial begin dbg_x_done = 0; dbg_xb_done = 0; end
    always @(posedge clk) begin
        if ($test$plusargs("DBG")) begin
            if (!dbg_x_done && u_dut.u_core.state == 6'd2) begin
                dbg_x_done <= 1;
                $display("[dbg-x w0..3] %h %h %h %h",
                         u_dut.u_spm.act_mem[0], u_dut.u_spm.act_mem[1],
                         u_dut.u_spm.act_mem[2], u_dut.u_spm.act_mem[3]);
            end
            if (!dbg_xb_done && u_dut.u_core.u_sfu.state == 6'd3) begin
                $display("[dbg-rms] cnt=%0d raddr=%0d rdata=%h sumsq=%0d",
                         u_dut.u_core.u_sfu.cnt,
                         u_dut.u_core.u_sfu.act_raddr_o,
                         u_dut.u_core.u_sfu.act_rdata_i,
                         u_dut.u_core.u_sfu.sumsq);
            end
            if (!dbg_xb_done && u_dut.u_core.state == 6'd3) begin
                dbg_xb_done <= 1;
                $display("[dbg-xb w8..11] %h %h %h %h",
                         u_dut.u_spm.act_mem[8], u_dut.u_spm.act_mem[9],
                         u_dut.u_spm.act_mem[10], u_dut.u_spm.act_mem[11]);
                $display("[dbg-sfu] state=%0d sumsq=%0d den=%0d quo=%0d inv=%0d gain0=%0d gbuf0=%0d",
                         u_dut.u_core.u_sfu.state,
                         u_dut.u_core.u_sfu.sumsq,
                         u_dut.u_core.u_sfu.dv_den,
                         u_dut.u_core.u_sfu.dv_quo,
                         u_dut.u_core.u_sfu.inv_rms,
                         u_dut.u_spm.vec_mem[0] & 16'hFFFF,
                         u_dut.u_core.u_sfu.gbuf[0]);
            end
        end
    end

    // v1.2 numerical first-divergence trace. The dedicated trace wrapper runs
    // four tokens once; normal regressions remain quiet.
    always @(posedge clk) begin
        if (DEFAULT_TRACE_NUM && u_dut.u_core.phase == 1'b0) begin
            if (u_dut.u_core.state == 6'd3 && u_dut.u_core.qkv_i == 2'd0)
                $display("[trace p=%0d l=%0d tag=XB] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[8], u_dut.u_spm.act_mem[9],
                    u_dut.u_spm.act_mem[10], u_dut.u_spm.act_mem[11],
                    u_dut.u_spm.act_mem[12], u_dut.u_spm.act_mem[13],
                    u_dut.u_spm.act_mem[14], u_dut.u_spm.act_mem[15]);
            if (u_dut.u_core.state == 6'd5) begin
                $display("[trace p=%0d l=%0d tag=Q] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[16], u_dut.u_spm.act_mem[17],
                    u_dut.u_spm.act_mem[18], u_dut.u_spm.act_mem[19],
                    u_dut.u_spm.act_mem[20], u_dut.u_spm.act_mem[21],
                    u_dut.u_spm.act_mem[22], u_dut.u_spm.act_mem[23]);
                $display("[trace p=%0d l=%0d tag=KT] %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[24], u_dut.u_spm.act_mem[25],
                    u_dut.u_spm.act_mem[26], u_dut.u_spm.act_mem[27]);
                $display("[trace p=%0d l=%0d tag=V] %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[32], u_dut.u_spm.act_mem[33],
                    u_dut.u_spm.act_mem[34], u_dut.u_spm.act_mem[35]);
            end
            if (u_dut.u_core.state == 6'd9)
                $display("[trace p=%0d l=%0d tag=ATT] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[360], u_dut.u_spm.act_mem[361],
                    u_dut.u_spm.act_mem[362], u_dut.u_spm.act_mem[363],
                    u_dut.u_spm.act_mem[364], u_dut.u_spm.act_mem[365],
                    u_dut.u_spm.act_mem[366], u_dut.u_spm.act_mem[367]);
            if (u_dut.u_core.state == 6'd11)
                $display("[trace p=%0d l=%0d tag=RES1] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[0], u_dut.u_spm.act_mem[1],
                    u_dut.u_spm.act_mem[2], u_dut.u_spm.act_mem[3],
                    u_dut.u_spm.act_mem[4], u_dut.u_spm.act_mem[5],
                    u_dut.u_spm.act_mem[6], u_dut.u_spm.act_mem[7]);
            if ((u_dut.u_core.state == 6'd2 && u_dut.u_core.layer != 3'd0) ||
                u_dut.u_core.state == 6'd17)
                $display("[trace p=%0d l=%0d tag=RES2] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o, u_dut.u_core.layer,
                    u_dut.u_spm.act_mem[0], u_dut.u_spm.act_mem[1],
                    u_dut.u_spm.act_mem[2], u_dut.u_spm.act_mem[3],
                    u_dut.u_spm.act_mem[4], u_dut.u_spm.act_mem[5],
                    u_dut.u_spm.act_mem[6], u_dut.u_spm.act_mem[7]);
            if (u_dut.u_core.state == 6'd18)
                $display("[trace p=%0d l=5 tag=RMSF] %h %h %h %h %h %h %h %h",
                    u_dut.u_core.seq_pos_o,
                    u_dut.u_spm.act_mem[8], u_dut.u_spm.act_mem[9],
                    u_dut.u_spm.act_mem[10], u_dut.u_spm.act_mem[11],
                    u_dut.u_spm.act_mem[12], u_dut.u_spm.act_mem[13],
                    u_dut.u_spm.act_mem[14], u_dut.u_spm.act_mem[15]);
        end
    end

    // per-state cycle histogram for throughput analysis
    integer state_cycles [0:63];
    integer sc_i;
    initial begin
        for (sc_i = 0; sc_i < 64; sc_i = sc_i + 1) state_cycles[sc_i] = 0;
    end
    always @(posedge clk) begin
        if (u_dut.u_core.busy_o)
            state_cycles[u_dut.u_core.state] = state_cycles[u_dut.u_core.state] + 1;
    end

    task print_state_hist;
        integer s;
        begin
            for (s = 0; s < 22; s = s + 1) begin
                if (state_cycles[s] != 0)
                    $display("[hist] state %0d: %0d cycles (%0d/token)", s,
                             state_cycles[s], state_cycles[s]/gen_tokens);
            end
        end
    endtask

    always @(posedge clk) begin
        if (capture_enable && u_dut.token_valid_set) begin
            // Golden is for the BOS (seed=1) QAT trajectory only.
            if (run_phase == 1 && have_wimage && have_vimage &&
                check_golden && seed_token == 9'd1 &&
                tok_seen < 64 && u_dut.token_out !== golden_token(tok_seen)) begin
                errors = errors + 1;
                $display("[%0t] FAIL: fixed-model token %0d mismatch (RTL=%0d golden=%0d)",
                         $time, tok_seen, u_dut.token_out,
                         golden_token(tok_seen));
            end
            if (tok_seen < gen_tokens) begin
                if (run_phase == 1) tok_run1[tok_seen] = u_dut.token_out;
                else                tok_run2[tok_seen] = u_dut.token_out;
            end
            tok_seen = tok_seen + 1;
            if (run_phase == 1)
                $display("[tok %0d] %0d", tok_seen-1, u_dut.token_out);
            if (u_dut.token_out >= 512) begin
                errors = errors + 1;
                $display("[%0t] FAIL: illegal token %0d", $time,
                         u_dut.token_out);
            end
        end
    end

    task run_decode;
        integer wait_cycles;
        begin
            tok_seen = 0;
            mm_wr(CSR_BASE + REG_PERF_CLR, 32'd1);
            mm_wr(CSR_BASE + REG_TOKEN_IN, {23'd0, seed_token}); // default BOS=1
            mm_wr(CSR_BASE + REG_GEN_CFG, (gen_tokens-1) | (SM_SHIFT << 17));
            // DEC_CFG: [7:0]rep_pen | [8]adapt_en | [12:9]norep_win
            mm_wr(CSR_BASE + REG_DEC_CFG,
                  {19'd0, norep_win, adapt_en, rep_pen});
            mm_wr(CSR_BASE + REG_CTRL, 32'h0000_0009);      // irq_en|start
            wait_cycles = 0;
            rd = 32'd0;
            while (rd[1] !== 1'b1 && wait_cycles < wait_limit) begin
                mm_rd(CSR_BASE + REG_STATUS, rd, rerr);
                wait_cycles = wait_cycles + 1;
            end
            if (rd[1] !== 1'b1) begin
                fail("decode timeout (STATUS.done never set)");
                $display("[dbg] core.state=%0d sfu.state=%0d mv_state=%0d seq_pos=%0d layer=%0d head=%0d",
                         u_dut.u_core.state, u_dut.u_core.u_sfu.state,
                         u_dut.u_core.mv_state, u_dut.seq_pos,
                         u_dut.u_core.layer, u_dut.u_core.head);
            end
            if (rd[2] === 1'b1) begin
                fail("decode raised STATUS.error");
            end
        end
    endtask

    // ------------------------------------------------------------------
    // Main sequence
    // ------------------------------------------------------------------
    integer cyc_lo, cyc_hi, mac_lo, mac_hi, tok_total;
    real    tok_per_s;

    initial begin
        errors    = 0;
        run_phase = 1;
        tok_seen  = 0;
        gen_tokens = DEFAULT_GEN_TOKENS;
        long_mode  = DEFAULT_LONG_MODE;
        test_name  = "";
        seed_token = 9'd1;
        check_golden = 1'b1;
        // DEC_CFG defaults match R4 golden (rep_pen=32, adapt/norep off).
        rep_pen     = 8'd32;
        adapt_en    = 1'b0;
        norep_win   = 4'd0;
        dec_profile = "golden";
        if ($value$plusargs("TESTNAME=%s", test_name) &&
            test_name == "long512") begin
            gen_tokens = MAX_GEN_TOKENS;
            long_mode  = 1'b1;
        end
        if ($value$plusargs("SEED_TOKEN=%d", seed_tmp)) begin
            if (seed_tmp < 0) seed_tmp = 0;
            if (seed_tmp > 511) seed_tmp = 511;
            seed_token = seed_tmp[8:0];
            // Alternate prompts are exploratory; do not enforce BOS golden.
            if (seed_token != 9'd1)
                check_golden = 1'b0;
        end
        // Profile first; explicit field plusargs override.
        if ($value$plusargs("DEC_PROFILE=%s", dec_profile)) begin
            if (dec_profile == "golden") begin
                rep_pen = 8'd32; adapt_en = 1'b0; norep_win = 4'd0;
            end else if (dec_profile == "mid") begin
                rep_pen = 8'd48; adapt_en = 1'b0; norep_win = 4'd0;
            end else if (dec_profile == "long") begin
                rep_pen = 8'd64; adapt_en = 1'b1; norep_win = 4'd12;
            end else begin
                $display("[cfg] WARN unknown DEC_PROFILE=%0s; keeping golden",
                         dec_profile);
                dec_profile = "golden";
            end
        end
        if ($value$plusargs("REP_PEN=%d", rep_pen_i)) begin
            if (rep_pen_i < 0) rep_pen_i = 0;
            if (rep_pen_i > 255) rep_pen_i = 255;
            rep_pen = rep_pen_i[7:0];
        end
        if ($value$plusargs("ADAPT_EN=%d", adapt_en_i)) begin
            adapt_en = (adapt_en_i != 0);
        end
        if ($value$plusargs("NOREP_WIN=%d", norep_win_i)) begin
            if (norep_win_i < 0) norep_win_i = 0;
            if (norep_win_i > 15) norep_win_i = 15;
            norep_win = norep_win_i[3:0];
        end
        // Non-default decode policy cannot match the fixed R4 golden trail.
        if ((rep_pen != 8'd32) || adapt_en || (norep_win != 4'd0))
            check_golden = 1'b0;
        wait_limit = long_mode ? 50000000 : 4000000;
        $display("[cfg] TESTNAME=%0s gen_tokens=%0d seed_token=%0d check_golden=%0d",
                 test_name, gen_tokens, seed_token, check_golden);
        $display("[cfg] DEC_PROFILE=%0s DEC_CFG rep_pen=%0d adapt_en=%0d norep_win=%0d",
                 dec_profile, rep_pen, adapt_en, norep_win);
        capture_enable = 1'b0;
        mm_valid  = 1'b0;
        mm_write  = 1'b0;
        mm_addr   = 20'd0;
        mm_wdata  = 32'd0;
        mm_wstrb  = 4'h0;
        mac_clk_en   = 1'b0;
        mac_clear    = 1'b0;
        mac_grp_last = 1'b0;
        mac_scale_en = 1'b0;
        mac_w        = 512'd0;
        mac_x        = 64'd0;
        mac_scale    = 128'd0;
        rst_n = 1'b0;
        repeat (8) @(posedge clk);
        rst_n = 1'b1;
        repeat (4) @(posedge clk);

        // ---------------- T1: ID / VERSION ----------------
        mm_rd(CSR_BASE + REG_ID, rd, rerr);
        if (rd !== 32'h5354_4F52 || rerr) fail("ID mismatch");
        mm_rd(CSR_BASE + REG_VERSION, rd, rerr);
        if (rd !== 32'h0001_0000 || rerr) fail("VERSION mismatch");
        $display("[%0t] T1 ID/VERSION ok", $time);

        // ---------------- T2: MAC unit ----------------
        lfsr = 32'h1BAD_B005;
        mac_random_trial(1, 1);
        mac_random_trial(8, 1);
        mac_random_trial(3, 0);
        $display("[%0t] T2 MAC unit checks done (errors=%0d)", $time, errors);

        // ---------------- T3: full decode ----------------
        have_wimage = $value$plusargs("WIMAGE=%s", wimage);
        have_vimage = $value$plusargs("VIMAGE=%s", vimage);
        if (have_wimage) begin
            $display("[%0t] loading WBUF image %0s", $time, wimage);
            $readmemh(wimage, u_dut.u_spm.wbuf_mem);
        end else begin
            load_wbuf_lfsr;
        end
        if (have_vimage) begin
            $display("[%0t] loading VECBUF image %0s", $time, vimage);
            $readmemh(vimage, u_dut.u_spm.vec_mem);
        end else begin
            load_vecbuf;
        end
        $display("[%0t] buffers loaded", $time);

        // Physical capacities stay unchanged; all 512-position tails fit.
        if (WBUF_LAST_W >= WBUF_CAP_W || KV_LAST_W >= 3968 ||
            ACT_LAST_W >= 512 || VEC_LAST_W >= 1024)
            fail("512-position layout exceeds an SRAM bank");
        check_rope_pos(0);
        check_rope_pos(383);
        check_rope_pos(511);
        $display("[%0t] T3 layout boundaries ok", $time);

        capture_enable = 1'b1;
        run_phase = 1;
        run_decode;
        if (tok_seen != gen_tokens) begin
            errors = errors + 1;
            $display("[%0t] FAIL: expected %0d tokens, saw %0d",
                     $time, gen_tokens, tok_seen);
        end
        mm_rd(CSR_BASE + REG_CYCLE_LO, cyc_lo, rerr);
        mm_rd(CSR_BASE + REG_CYCLE_HI, cyc_hi, rerr);
        mm_rd(CSR_BASE + REG_MAC_LO, mac_lo, rerr);
        mm_rd(CSR_BASE + REG_MAC_HI, mac_hi, rerr);
        mm_rd(CSR_BASE + REG_TOKEN_CT, tok_total, rerr);
        if (tok_total != gen_tokens)
            fail("TOKEN_CNT mismatch");
        mm_rd(CSR_BASE + REG_SEQ_POS, rd, rerr);
        if (rd !== gen_tokens)
            fail("SEQ_POS mismatch");
        print_state_hist;
        tok_per_s = (gen_tokens * 1.0e9) / (cyc_lo * 10.0);
        $display("[%0t] decode run1: %0d tokens in %0d cycles -> %0.1f tok/s, MAC util %0.1f%%",
                 $time, gen_tokens, cyc_lo, tok_per_s,
                 (mac_lo * 100.0) / (cyc_lo * 64.0));
        if (tok_per_s < 8700.0) begin
            errors = errors + 1;
            $display("[%0t] FAIL: throughput %0.1f tok/s < 8700 target",
                     $time, tok_per_s);
        end

        // Default regression proves determinism. The long boundary test runs
        // once so it reaches position 511 without doubling multi-minute time.
        if (!long_mode) begin
            run_phase = 2;
            run_decode;
            for (i = 0; i < gen_tokens; i = i + 1) begin
                if (tok_run1[i] !== tok_run2[i]) begin
                    errors = errors + 1;
                    $display("[%0t] FAIL: nondeterministic token %0d (%0d vs %0d)",
                             $time, i, tok_run1[i], tok_run2[i]);
                end
            end
        end else begin
            $display("[%0t] T3 long-context single-run requested length reached (%0d tokens)",
                     $time, gen_tokens);
        end
        $display("[%0t] T3 decode/determinism/throughput done (errors=%0d)",
                 $time, errors);

        // ---------------- T4: error injection ----------------
        mm_rd(20'h7_0000, rd, rerr);
        if (!rerr) fail("invalid address did not raise mm_error");
        mm_rd(CSR_BASE + REG_ID, rd, rerr);
        if (rd !== 32'h5354_4F52 || rerr)
            fail("CSR broken after error injection");
        $display("[%0t] T4 error injection ok", $time);

        // ---------------- dump long token trail for host detok ----------------
        begin
            integer fd, ti;
            fd = $fopen("rtl_tokens_long.json", "w");
            if (fd) begin
                // seed TOKEN_IN then generated tokens from run1
                $fwrite(fd, "[%0d", seed_token);
                for (ti = 0; ti < gen_tokens; ti = ti + 1)
                    $fwrite(fd, ",%0d", tok_run1[ti]);
                $fwrite(fd, "]\n");
                $fclose(fd);
                $display("wrote rtl_tokens_long.json (%0d ids incl seed=%0d)",
                         gen_tokens + 1, seed_token);
            end
        end

        // ---------------- summary ----------------
        if (errors == 0) begin
            $display("TB_STORIES260K PASSED");
            $display("RESULT: ALL TESTS PASS");
        end else begin
            $display("TB_STORIES260K FAILED errors=%0d", errors);
            $display("RESULT: TESTS FAILED");
        end
        $finish;
    end

    // global watchdog
    initial begin
        #1_000_000_000;
        $display("TB_STORIES260K FAILED errors=%0d (global watchdog)", errors+1);
        $finish;
    end

endmodule

// Dedicated registered-simulation top for the full checkpoint context. Using
// a top-level parameter override avoids relying on runner-specific plusargs.
module tb_stories260k_long512;
    tb_stories260k #(
        .DEFAULT_GEN_TOKENS (512),
        .DEFAULT_LONG_MODE  (1)
    ) u_tb();
endmodule

// Mid-context points for multi-length quality regression (Round-4 gates).
module tb_stories260k_long128;
    tb_stories260k #(
        .DEFAULT_GEN_TOKENS (128),
        .DEFAULT_LONG_MODE  (1)
    ) u_tb();
endmodule

module tb_stories260k_long256;
    tb_stories260k #(
        .DEFAULT_GEN_TOKENS (256),
        .DEFAULT_LONG_MODE  (1)
    ) u_tb();
endmodule

module tb_stories260k_trace;
    tb_stories260k #(
        .DEFAULT_GEN_TOKENS (4),
        .DEFAULT_LONG_MODE  (1),
        .DEFAULT_TRACE_NUM  (1)
    ) u_tb();
endmodule
