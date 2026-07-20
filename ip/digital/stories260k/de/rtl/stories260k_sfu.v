//============================================================================
// Module     : stories260k_sfu
// Function   : Special-function unit: vector ops around the MAC array
//
// Ops: EMBED (INT4 embedding-row dequant), RMSNORM, ROPE, SOFTMAX (with K/V
// scale folding and deferred denominator), SWIGLU, RESADD, KVAPPEND (INT8 ->
// INT4 quantization with power-of-two per-pos scale). Shared micro-engines:
// 16-cycle integer square root and 26-cycle restoring divider. exp/sigmoid
// use small generated LUTs (Q4 input domain, see docs/design_spec.md).
//
// All buffer ports are combinational-read; the core arbitrates SFU vs MVM.
//============================================================================

module stories260k_sfu (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         soft_reset_i,
    input  wire         start_i,
    input  wire [4:0]   op_i,
    input  wire [11:0]  p0_i,
    input  wire [11:0]  p1_i,
    input  wire [8:0]   p2_i,
    output reg          busy_o,
    output reg          done_o,

    output wire [8:0]   act_raddr_o,
    input  wire [63:0]  act_rdata_i,
    output wire         act_we_o,
    output wire [8:0]   act_waddr_o,
    output wire [63:0]  act_wdata_o,
    output wire [7:0]   act_wstrb_o,

    output wire [9:0]   vec_raddr_o,
    input  wire [63:0]  vec_rdata_i,
    output reg          vec_we_o,
    output reg  [9:0]   vec_waddr_o,
    output reg  [63:0]  vec_wdata_o,

    output wire [11:0]  kv_raddr_o,
    input  wire [255:0] kv_rdata_i,
    output reg          kv_we_o,
    output reg  [11:0]  kv_waddr_o,
    output reg  [255:0] kv_wdata_o,
    output reg  [31:0]  kv_wstrb_o,

    output wire [12:0]  wbuf_raddr_o,
    input  wire [255:0] wbuf_rdata_i
);

    // op codes
    localparam [4:0] OP_EMBED    = 5'd1;
    localparam [4:0] OP_RMSNORM  = 5'd2;
    localparam [4:0] OP_ROPE     = 5'd3;
    localparam [4:0] OP_SOFTMAX  = 5'd4;
    localparam [4:0] OP_SWIGLU   = 5'd5;
    localparam [4:0] OP_RESADD   = 5'd6;
    localparam [4:0] OP_KVAPPEND = 5'd7;

    // fixed ACT word offsets (8-byte words)
    localparam [8:0] AW_X     = 9'd0;
    localparam [8:0] AW_KT    = 9'd24;
    localparam [8:0] AW_V     = 9'd32;
    localparam [8:0] AW_SCORE = 9'd40;
    localparam [8:0] AW_PR    = 9'd296;

    // KV layer-block offsets in 32B words (GQA: 4 KV heads x 512 pos)
    // [K data 4x64][K scales 4x32][V data 4x64][V scales 4x32] = 768 words
    localparam [11:0] KV_KSC_OFF = 12'd256;
    localparam [11:0] KV_V_OFF   = 12'd384;
    localparam [11:0] KV_VSC_OFF = 12'd640;

    // VEC words
    localparam [9:0] VW_RQ     = 10'd176;  // requant table base
    localparam [9:0] RQ_ATT_SLOT = 10'd35; // dynamic attention recip slot

    // WBUF words 4374..4629: two positions per word, each {sin, cos} 128b.
    localparam [12:0] WROPE_WORD = 13'd4374;

    // WBUF embedding scale region: byte 0x20200 -> 32B word 4112
    localparam [12:0] WSC_EMB_WORD = 13'd4112;

    // states
    localparam [5:0] S_IDLE     = 6'd0;
    localparam [5:0] S_EMB_SC   = 6'd1;
    localparam [5:0] S_EMB_RD   = 6'd2;
    localparam [5:0] S_RMS_RD   = 6'd3;
    localparam [5:0] S_RMS_DIV  = 6'd4;
    localparam [5:0] S_RMS_GAIN = 6'd5;
    localparam [5:0] S_RMS_WR   = 6'd6;
    localparam [5:0] S_ROPE_TAB = 6'd7;
    localparam [5:0] S_ROPE_RD  = 6'd8;
    localparam [5:0] S_ROPE_WR  = 6'd9;
    localparam [5:0] S_SM_SC    = 6'd10;
    localparam [5:0] S_SM_EXP   = 6'd11;
    localparam [5:0] S_SM_DIV   = 6'd12;
    localparam [5:0] S_SM_RQ    = 6'd13;
    localparam [5:0] S_GLU      = 6'd14;
    localparam [5:0] S_RES      = 6'd15;
    localparam [5:0] S_KVA_RD   = 6'd16;
    localparam [5:0] S_KVA_KW   = 6'd17;
    localparam [5:0] S_KVA_KSW  = 6'd18;
    localparam [5:0] S_KVA_VW   = 6'd19;
    localparam [5:0] S_KVA_VSW  = 6'd20;
    localparam [5:0] S_SQRT     = 6'd21;
    localparam [5:0] S_DIV      = 6'd22;
    localparam [5:0] S_DONE     = 6'd23;

    reg [5:0]  state;
    reg [5:0]  ret_state;
    reg [11:0] p0, p1;
    reg [8:0]  p2;
    reg [15:0] cnt;
    reg        sub;

    reg signed [7:0]  ibuf [0:127];
    reg        [15:0] gbuf [0:63];
    reg signed [31:0] sbuf [0:511];

    reg [31:0] sumsq;
    reg [15:0] inv_rms;
    reg signed [31:0] smax;
    reg [31:0] sum_exp;

    // sqrt micro-engine (19-bit rem: rem < 2*root+1 << 2^18 in operation)
    reg [18:0] sq_rem;
    reg [31:0] sq_val;
    reg [15:0] sq_root;
    reg [4:0]  sq_cnt;

    // div micro-engine (15-bit rem: divisor < 2^15 by design)
    reg [31:0] dv_num;
    reg [15:0] dv_den;
    reg [14:0] dv_rem;
    reg [26:0] dv_quo;
    reg [5:0]  dv_cnt;

    // rope table registers (4 pairs x int16)
    reg [63:0] rope_cs [0:1];

    // kv append registers
    reg [3:0]  hcnt;
    reg [63:0] kreg, vreg;

    // softmax pack register
    reg [63:0] ppack;

    reg [15:0] emb_scale;

    // ------------------------------------------------------------------
    // LUTs (generated; Q4 input domain)
    // ------------------------------------------------------------------
    reg [7:0]  exp_tab [0:128];
    reg [15:0] sig_tab [0:128];

    initial begin
        exp_tab[0]=8'd0;    exp_tab[1]=8'd0;    exp_tab[2]=8'd0;    exp_tab[3]=8'd0;
        exp_tab[4]=8'd0;    exp_tab[5]=8'd0;    exp_tab[6]=8'd0;    exp_tab[7]=8'd0;
        exp_tab[8]=8'd0;    exp_tab[9]=8'd0;    exp_tab[10]=8'd0;   exp_tab[11]=8'd0;
        exp_tab[12]=8'd0;   exp_tab[13]=8'd0;   exp_tab[14]=8'd0;   exp_tab[15]=8'd0;
        exp_tab[16]=8'd0;   exp_tab[17]=8'd0;   exp_tab[18]=8'd0;   exp_tab[19]=8'd0;
        exp_tab[20]=8'd0;   exp_tab[21]=8'd0;   exp_tab[22]=8'd0;   exp_tab[23]=8'd0;
        exp_tab[24]=8'd0;   exp_tab[25]=8'd0;   exp_tab[26]=8'd0;   exp_tab[27]=8'd0;
        exp_tab[28]=8'd0;   exp_tab[29]=8'd0;   exp_tab[30]=8'd0;   exp_tab[31]=8'd0;
        exp_tab[32]=8'd0;   exp_tab[33]=8'd0;   exp_tab[34]=8'd0;   exp_tab[35]=8'd0;
        exp_tab[36]=8'd0;   exp_tab[37]=8'd0;   exp_tab[38]=8'd0;   exp_tab[39]=8'd0;
        exp_tab[40]=8'd1;   exp_tab[41]=8'd1;   exp_tab[42]=8'd1;   exp_tab[43]=8'd1;
        exp_tab[44]=8'd1;   exp_tab[45]=8'd1;   exp_tab[46]=8'd1;   exp_tab[47]=8'd1;
        exp_tab[48]=8'd1;   exp_tab[49]=8'd1;   exp_tab[50]=8'd1;   exp_tab[51]=8'd1;
        exp_tab[52]=8'd1;   exp_tab[53]=8'd1;   exp_tab[54]=8'd1;   exp_tab[55]=8'd1;
        exp_tab[56]=8'd1;   exp_tab[57]=8'd2;   exp_tab[58]=8'd2;   exp_tab[59]=8'd2;
        exp_tab[60]=8'd2;   exp_tab[61]=8'd2;   exp_tab[62]=8'd2;   exp_tab[63]=8'd2;
        exp_tab[64]=8'd2;   exp_tab[65]=8'd2;   exp_tab[66]=8'd3;   exp_tab[67]=8'd3;
        exp_tab[68]=8'd3;   exp_tab[69]=8'd3;   exp_tab[70]=8'd3;   exp_tab[71]=8'd4;
        exp_tab[72]=8'd4;   exp_tab[73]=8'd4;   exp_tab[74]=8'd4;   exp_tab[75]=8'd5;
        exp_tab[76]=8'd5;   exp_tab[77]=8'd5;   exp_tab[78]=8'd6;   exp_tab[79]=8'd6;
        exp_tab[80]=8'd6;   exp_tab[81]=8'd7;   exp_tab[82]=8'd7;   exp_tab[83]=8'd8;
        exp_tab[84]=8'd8;   exp_tab[85]=8'd9;   exp_tab[86]=8'd9;   exp_tab[87]=8'd10;
        exp_tab[88]=8'd10;  exp_tab[89]=8'd11;  exp_tab[90]=8'd12;  exp_tab[91]=8'd13;
        exp_tab[92]=8'd13;  exp_tab[93]=8'd14;  exp_tab[94]=8'd15;  exp_tab[95]=8'd16;
        exp_tab[96]=8'd17;  exp_tab[97]=8'd18;  exp_tab[98]=8'd19;  exp_tab[99]=8'd21;
        exp_tab[100]=8'd22; exp_tab[101]=8'd23; exp_tab[102]=8'd25; exp_tab[103]=8'd27;
        exp_tab[104]=8'd28; exp_tab[105]=8'd30; exp_tab[106]=8'd32; exp_tab[107]=8'd34;
        exp_tab[108]=8'd36; exp_tab[109]=8'd39; exp_tab[110]=8'd41; exp_tab[111]=8'd44;
        exp_tab[112]=8'd47; exp_tab[113]=8'd50; exp_tab[114]=8'd53; exp_tab[115]=8'd56;
        exp_tab[116]=8'd60; exp_tab[117]=8'd64; exp_tab[118]=8'd68; exp_tab[119]=8'd72;
        exp_tab[120]=8'd77; exp_tab[121]=8'd82; exp_tab[122]=8'd87; exp_tab[123]=8'd93;
        exp_tab[124]=8'd99; exp_tab[125]=8'd105;exp_tab[126]=8'd112;exp_tab[127]=8'd119;
        exp_tab[128]=8'd127;

        sig_tab[0]=16'd16384;  sig_tab[1]=16'd16895;  sig_tab[2]=16'd17406;  sig_tab[3]=16'd17915;
        sig_tab[4]=16'd18421;  sig_tab[5]=16'd18923;  sig_tab[6]=16'd19420;  sig_tab[7]=16'd19911;
        sig_tab[8]=16'd20396;  sig_tab[9]=16'd20874;  sig_tab[10]=16'd21343; sig_tab[11]=16'd21804;
        sig_tab[12]=16'd22255; sig_tab[13]=16'd22696; sig_tab[14]=16'd23126; sig_tab[15]=16'd23546;
        sig_tab[16]=16'd23955; sig_tab[17]=16'd24351; sig_tab[18]=16'd24736; sig_tab[19]=16'd25109;
        sig_tab[20]=16'd25470; sig_tab[21]=16'd25818; sig_tab[22]=16'd26154; sig_tab[23]=16'd26478;
        sig_tab[24]=16'd26789; sig_tab[25]=16'd27089; sig_tab[26]=16'd27376; sig_tab[27]=16'd27652;
        sig_tab[28]=16'd27916; sig_tab[29]=16'd28169; sig_tab[30]=16'd28410; sig_tab[31]=16'd28641;
        sig_tab[32]=16'd28861; sig_tab[33]=16'd29071; sig_tab[34]=16'd29271; sig_tab[35]=16'd29462;
        sig_tab[36]=16'd29643; sig_tab[37]=16'd29815; sig_tab[38]=16'd29979; sig_tab[39]=16'd30134;
        sig_tab[40]=16'd30281; sig_tab[41]=16'd30421; sig_tab[42]=16'd30554; sig_tab[43]=16'd30679;
        sig_tab[44]=16'd30798; sig_tab[45]=16'd30911; sig_tab[46]=16'd31017; sig_tab[47]=16'd31118;
        sig_tab[48]=16'd31213; sig_tab[49]=16'd31303; sig_tab[50]=16'd31388; sig_tab[51]=16'd31468;
        sig_tab[52]=16'd31544; sig_tab[53]=16'd31615; sig_tab[54]=16'd31683; sig_tab[55]=16'd31747;
        sig_tab[56]=16'd31807; sig_tab[57]=16'd31863; sig_tab[58]=16'd31916; sig_tab[59]=16'd31967;
        sig_tab[60]=16'd32014; sig_tab[61]=16'd32059; sig_tab[62]=16'd32101; sig_tab[63]=16'd32140;
        sig_tab[64]=16'd32178; sig_tab[65]=16'd32213; sig_tab[66]=16'd32246; sig_tab[67]=16'd32277;
        sig_tab[68]=16'd32306; sig_tab[69]=16'd32334; sig_tab[70]=16'd32360; sig_tab[71]=16'd32384;
        sig_tab[72]=16'd32407; sig_tab[73]=16'd32429; sig_tab[74]=16'd32449; sig_tab[75]=16'd32468;
        sig_tab[76]=16'd32486; sig_tab[77]=16'd32503; sig_tab[78]=16'd32519; sig_tab[79]=16'd32534;
        sig_tab[80]=16'd32548; sig_tab[81]=16'd32561; sig_tab[82]=16'd32573; sig_tab[83]=16'd32585;
        sig_tab[84]=16'd32596; sig_tab[85]=16'd32606; sig_tab[86]=16'd32616; sig_tab[87]=16'd32625;
        sig_tab[88]=16'd32634; sig_tab[89]=16'd32642; sig_tab[90]=16'd32649; sig_tab[91]=16'd32656;
        sig_tab[92]=16'd32663; sig_tab[93]=16'd32669; sig_tab[94]=16'd32675; sig_tab[95]=16'd32681;
        sig_tab[96]=16'd32686; sig_tab[97]=16'd32691; sig_tab[98]=16'd32695; sig_tab[99]=16'd32700;
        sig_tab[100]=16'd32704;sig_tab[101]=16'd32708;sig_tab[102]=16'd32711;sig_tab[103]=16'd32715;
        sig_tab[104]=16'd32718;sig_tab[105]=16'd32721;sig_tab[106]=16'd32724;sig_tab[107]=16'd32726;
        sig_tab[108]=16'd32729;sig_tab[109]=16'd32731;sig_tab[110]=16'd32733;sig_tab[111]=16'd32735;
        sig_tab[112]=16'd32737;sig_tab[113]=16'd32739;sig_tab[114]=16'd32741;sig_tab[115]=16'd32742;
        sig_tab[116]=16'd32744;sig_tab[117]=16'd32745;sig_tab[118]=16'd32746;sig_tab[119]=16'd32748;
        sig_tab[120]=16'd32749;sig_tab[121]=16'd32750;sig_tab[122]=16'd32751;sig_tab[123]=16'd32752;
        sig_tab[124]=16'd32753;sig_tab[125]=16'd32754;sig_tab[126]=16'd32755;sig_tab[127]=16'd32755;
        sig_tab[128]=16'd32756;
    end

    // ------------------------------------------------------------------
    // Helper functions
    // ------------------------------------------------------------------
    function signed [7:0] sat8;
        input signed [47:0] v;
        begin
            if (v > 48'sd127)       sat8 = 8'sd127;
            else if (v < -48'sd128) sat8 = -8'sd128;
            else                    sat8 = v[7:0];
        end
    endfunction

    function [3:0] nib4;
        input signed [7:0] v;
        begin
            if (v > 8'sd7)       nib4 = 4'h7;
            else if (v < -8'sd8) nib4 = 4'h8;
            else                 nib4 = v[3:0];
        end
    endfunction

    // Signed round-half-up before INT4 saturation. The 9-bit temporary keeps
    // +half from overflowing for positive INT8 inputs.
    function [3:0] nib4_round;
        input signed [7:0] v;
        input [3:0] sh;
        reg signed [8:0] r;
        begin
            r = {v[7], v};
            if (sh != 4'd0) r = r + (9'sd1 <<< (sh - 4'd1));
            r = r >>> sh;
            if (r > 9'sd7)       nib4_round = 4'h7;
            else if (r < -9'sd8) nib4_round = 4'h8;
            else                 nib4_round = r[3:0];
        end
    endfunction

    // power-of-two Q4.12 scale 1<<(s+9), s in 0..5
    function [15:0] qscale;
        input [3:0] s;
        begin
            case (s)
                4'd0:    qscale = 16'h0200;
                4'd1:    qscale = 16'h0400;
                4'd2:    qscale = 16'h0800;
                4'd3:    qscale = 16'h1000;
                4'd4:    qscale = 16'h2000;
                default: qscale = 16'h4000;
            endcase
        end
    endfunction

    function [7:0] abs8;
        input signed [7:0] v;
        begin
            abs8 = (v < 0) ? ((v == -8'sd128) ? 8'd128 : -v) : v;
        end
    endfunction

    function [7:0] max8abs;
        input [63:0] w;
        integer j;
        reg [7:0] m;
        begin
            m = 8'd0;
            for (j = 0; j < 8; j = j + 1)
                if (abs8(w[j*8 +: 8]) > m) m = abs8(w[j*8 +: 8]);
            max8abs = m;
        end
    endfunction

    function [2:0] msb7;
        input [7:0] v;
        begin
            casez (v)
                8'b1???????: msb7 = 3'd7;
                8'b01??????: msb7 = 3'd6;
                8'b001?????: msb7 = 3'd5;
                8'b0001????: msb7 = 3'd4;
                8'b00001???: msb7 = 3'd3;
                8'b000001??: msb7 = 3'd2;
                8'b0000001?: msb7 = 3'd1;
                default:     msb7 = 3'd0;
            endcase
        end
    endfunction

    // sum of 8 signed squares from a 64-bit lane word
    function [31:0] sq8;
        input [63:0] w;
        integer j;
        integer xv;
        reg [31:0] acc;
        begin
            acc = 32'd0;
            for (j = 0; j < 8; j = j + 1) begin
                xv  = {{24{w[j*8+7]}}, w[j*8 +: 8]};
                acc = acc + (xv * xv);
            end
            sq8 = acc;
        end
    endfunction

    // sqrt iteration wires (4 iterations unrolled per cycle)
    wire [20:0] s1_rem   = {sq_rem[18:0], sq_val[31:30]};
    wire [20:0] s1_trial = {3'd0, sq_root, 2'b01};
    wire        s1_take  = (s1_rem >= s1_trial);
    wire [20:0] s1_rdif  = s1_rem - s1_trial;
    wire [18:0] s1_remo  = s1_take ? s1_rdif[18:0] : s1_rem[18:0];
    wire [15:0] s1_root  = {sq_root[14:0], s1_take};
    wire [31:0] s1_val   = {sq_val[29:0], 2'b00};

    wire [20:0] s2_rem   = {s1_remo[18:0], s1_val[31:30]};
    wire [20:0] s2_trial = {3'd0, s1_root, 2'b01};
    wire        s2_take  = (s2_rem >= s2_trial);
    wire [20:0] s2_rdif  = s2_rem - s2_trial;
    wire [18:0] s2_remo  = s2_take ? s2_rdif[18:0] : s2_rem[18:0];
    wire [15:0] s2_root  = {s1_root[14:0], s2_take};
    wire [31:0] s2_val   = {s1_val[29:0], 2'b00};

    wire [20:0] s3_rem   = {s2_remo[18:0], s2_val[31:30]};
    wire [20:0] s3_trial = {3'd0, s2_root, 2'b01};
    wire        s3_take  = (s3_rem >= s3_trial);
    wire [20:0] s3_rdif  = s3_rem - s3_trial;
    wire [18:0] s3_remo  = s3_take ? s3_rdif[18:0] : s3_rem[18:0];
    wire [15:0] s3_root  = {s2_root[14:0], s3_take};
    wire [31:0] s3_val   = {s2_val[29:0], 2'b00};

    wire [20:0] s4_rem   = {s3_remo[18:0], s3_val[31:30]};
    wire [20:0] s4_trial = {3'd0, s3_root, 2'b01};
    wire        s4_take  = (s4_rem >= s4_trial);
    wire [20:0] s4_rdif  = s4_rem - s4_trial;
    wire [18:0] s4_remo  = s4_take ? s4_rdif[18:0] : s4_rem[18:0];
    wire [15:0] s4_root  = {s3_root[14:0], s4_take};

    // div iteration wires (2 iterations unrolled per cycle)
    wire [15:0] d1_rem   = {dv_rem[14:0], dv_num[31]};
    wire        d1_take  = (d1_rem >= dv_den);
    wire [15:0] d1_rdif  = d1_rem - dv_den;
    wire [14:0] d1_remo  = d1_take ? d1_rdif[14:0] : d1_rem[14:0];
    wire [31:0] d1_num   = {dv_num[30:0], 1'b0};

    wire [15:0] d2_rem   = {d1_remo[14:0], d1_num[31]};
    wire        d2_take  = (d2_rem >= dv_den);
    wire [15:0] d2_rdif  = d2_rem - dv_den;
    wire [14:0] d2_remo  = d2_take ? d2_rdif[14:0] : d2_rem[14:0];

    // provably-zero carry bits of the subtract wires (rem invariants)
    wire [9:0]  unused_rdif = {s1_rdif[20:19], s2_rdif[20:19],
                               s3_rdif[20:19], s4_rdif[20:19],
                               d1_rdif[15], d2_rdif[15]};

    // softmax dual-lane helpers (t and t+1 share one ACT word / scale word)
    // p2[1:0]=kv head, p2[5:2]=z downshift (score-domain to exp-domain)
    wire [15:0] cnt_p1   = cnt + 16'd1;
    wire        sm_last  = (cnt_p1 >= {4'd0, p0});
    wire        sm_two   = (cnt_p1 <= {4'd0, p0});
    wire [11:0] kvh32    = {10'd0, p2[1:0]} * 12'd32;
    wire [11:0] h64      = {8'd0, hcnt} * 12'd64;
    wire [11:0] h32      = {8'd0, hcnt} * 12'd32;
    wire [3:0]  z_shift  = p2[5:2];

    wire signed [31:0] sc_word0 = $signed(act_rdata_i[31:0]);
    wire signed [31:0] sc_word1 = $signed(act_rdata_i[63:32]);
    wire [15:0] sk_lane0 = kv_rdata_i[cnt[3:0]*16 +: 16];
    wire [15:0] sk_lane1 = kv_rdata_i[(cnt[3:0] + 4'd1)*16 +: 16];
    wire [15:0] sv_lane0 = kv_rdata_i[cnt[3:0]*16 +: 16];
    wire [15:0] sv_lane1 = kv_rdata_i[(cnt[3:0] + 4'd1)*16 +: 16];
    wire signed [47:0] sc_mul0 = sc_word0 * $signed({1'b0, sk_lane0});
    wire signed [47:0] sc_mul1 = sc_word1 * $signed({1'b0, sk_lane1});
    wire signed [47:0] sc_rnd0 = sc_mul0 + 48'sd1024;
    wire signed [47:0] sc_rnd1 = sc_mul1 + 48'sd1024;
    wire signed [31:0] sc_val0 = sc_rnd0[42:11];
    wire signed [31:0] sc_val1 = sc_rnd1[42:11];
    wire signed [31:0] sc_best = (sc_val0 > sc_val1) ? sc_val0 : sc_val1;
    // dropped product bits are intentional (>>>11 rounding shift)
    wire [15:0] unused_scmul0 = {sc_rnd0[47:43], sc_rnd0[10:0]};
    wire [15:0] unused_scmul1 = {sc_rnd1[47:43], sc_rnd1[10:0]};

    wire signed [31:0] z_full0 = (sbuf[cnt[8:0]] - smax) >>> z_shift;
    wire signed [31:0] z_full1 = (sbuf[cnt[8:0] + 9'd1] - smax) >>> z_shift;
    wire signed [7:0]  z_clamp0 = (z_full0 < -32'sd128) ? -8'sd128 :
                                  (z_full0 > 32'sd0) ? 8'sd0 : z_full0[7:0];
    wire signed [7:0]  z_clamp1 = (z_full1 < -32'sd128) ? -8'sd128 :
                                  (z_full1 > 32'sd0) ? 8'sd0 : z_full1[7:0];
    wire [7:0]         e_val0 = exp_tab[z_clamp0 + 8'd128];
    wire [7:0]         e_val1 = exp_tab[z_clamp1 + 8'd128];
    wire [23:0]        pp_mul0 = e_val0 * sv_lane0;
    wire [23:0]        pp_mul1 = e_val1 * sv_lane1;
    wire [7:0]         pp_val0 = sat8(({{24{1'b0}}, pp_mul0} + 48'd16384) >>> 15);
    wire [7:0]         pp_val1 = sat8(({{24{1'b0}}, pp_mul1} + 48'd16384) >>> 15);
    wire [14:0]        unused_ppmul0 = pp_mul0[14:0];
    wire [14:0]        unused_ppmul1 = pp_mul1[14:0];
    wire [31:0]        sum_exp_next = sum_exp + {24'd0, e_val0} +
                                      (sm_two ? {24'd0, e_val1} : 32'd0);

    // shared multiply temps (blocking, inside the FSM clocked block)

    // ------------------------------------------------------------------
    // Combinational read addresses (same-cycle data for capture loops)
    // ------------------------------------------------------------------
    reg [8:0]  act_raddr_c;
    reg [9:0]  vec_raddr_c;
    reg [11:0] kv_raddr_c;
    reg [12:0] wbuf_raddr_c;

    assign act_raddr_o  = act_raddr_c;
    assign vec_raddr_o  = vec_raddr_c;
    assign kv_raddr_o   = kv_raddr_c;
    assign wbuf_raddr_o = wbuf_raddr_c;

    always @* begin
        act_raddr_c  = 9'd0;
        vec_raddr_c  = 10'd0;
        kv_raddr_c   = 12'd0;
        wbuf_raddr_c = 13'd0;
        case (state)
            S_EMB_SC:   wbuf_raddr_c = WSC_EMB_WORD + {8'd0, p0[8:4]};
            S_EMB_RD:   wbuf_raddr_c = {4'd0, p0[8:3], 3'b000} + cnt[12:0];
            S_RMS_RD:   act_raddr_c  = p0[8:0] + {6'd0, cnt[2:0]};
            S_RMS_GAIN: vec_raddr_c  = p1[9:0] + {6'd0, cnt[3:0]};
            S_ROPE_TAB: wbuf_raddr_c = WROPE_WORD + {5'd0, p0[8:1]};
            S_ROPE_RD:  act_raddr_c  = (cnt[3] ? p2[8:0] : p1[8:0]) +
                                       {6'd0, cnt[2:0]};
            S_SM_SC: begin
                act_raddr_c = AW_SCORE + {1'b0, cnt[8:1]};
                kv_raddr_c  = p1[11:0] + KV_KSC_OFF + kvh32 + {7'd0, cnt[8:4]};
            end
            S_SM_EXP:   kv_raddr_c = p1[11:0] + KV_VSC_OFF + kvh32 +
                                     {7'd0, cnt[8:4]};
            S_GLU:      act_raddr_c = (sub ? p1[8:0] : p0[8:0]) +
                                      {4'd0, cnt[4:0]};
            S_RES:      act_raddr_c = (sub ? p1[8:0] : p0[8:0]) +
                                      {6'd0, cnt[2:0]};
            S_KVA_RD:   act_raddr_c = (sub ? AW_V : AW_KT) + {5'd0, hcnt};
            default: ;
        endcase
    end

    // ------------------------------------------------------------------
    // Combinational write datapath (consumes read data; separate from the
    // address block so no always block feeds back into itself)
    // ------------------------------------------------------------------
    reg        act_we_c;
    reg [8:0]  act_waddr_c;
    reg [7:0]  act_wstrb_c;
    reg [63:0] act_wdata_c;
    reg [31:0] kpack_c, vpack_c;
    reg [15:0] ks16_c, vs16_c;

    assign act_we_o     = act_we_c;
    assign act_waddr_o  = act_waddr_c;
    assign act_wstrb_o  = act_wstrb_c;
    assign act_wdata_o  = act_wdata_c;

    integer ei;
    reg signed [7:0]  x_lane;
    reg signed [15:0] g_lane;
    reg signed [47:0] mul_a;
    reg signed [47:0] mul_t;
    reg signed [47:0] mul_w;
    reg [3:0]         nib;
    reg [2:0]         ap_msb;
    reg [3:0]         ap_sh;
    reg [7:0]         ap_max;
    reg [31:0]        cnt_lane;

    always @* begin
        act_we_c     = 1'b0;
        act_waddr_c  = 9'd0;
        act_wstrb_c  = 8'd0;
        act_wdata_c  = 64'd0;
        kpack_c      = 32'd0;
        vpack_c      = 32'd0;
        ks16_c       = 16'h0200;
        vs16_c       = 16'h0200;
        x_lane       = 8'sd0;
        g_lane       = 16'sd0;
        mul_a        = 48'sd0;
        mul_t        = 48'sd0;
        mul_w        = 48'sd0;
        nib          = 4'd0;
        ap_msb       = 3'd0;
        ap_sh        = 4'd0;
        ap_max       = 8'd0;
        cnt_lane     = {29'd0, cnt[2:0]};
        case (state)
            S_EMB_RD: begin
                act_we_c     = 1'b1;
                act_waddr_c  = AW_X + {6'd0, cnt[2:0]};
                act_wstrb_c  = 8'hFF;
                for (ei = 0; ei < 8; ei = ei + 1) begin
                    nib    = wbuf_rdata_i[p0[2:0]*32 + ei*4 +: 4];
                    x_lane = $signed({nib[3], nib[3], nib[3], nib[3], nib});
                    mul_a  = x_lane * $signed(emb_scale) + 48'sd2048;
                    act_wdata_c[ei*8 +: 8] = sat8(mul_a >>> 12);
                end
            end
            S_RMS_WR: begin
                act_we_c    = 1'b1;
                act_waddr_c = p2[8:0] + {6'd0, cnt[2:0]};
                act_wstrb_c = 8'hFF;
                for (ei = 0; ei < 8; ei = ei + 1) begin
                    mul_a = ibuf[cnt[2:0]*8 + ei] * $signed(gbuf[cnt[2:0]*8 + ei]);
                    mul_t = (mul_a + 48'sd8192) >>> 14;
                    mul_w = mul_t * $signed({1'b0, inv_rms}) + 48'sd1024;
                    act_wdata_c[ei*8 +: 8] = sat8(mul_w >>> 11);
                end
            end
            S_ROPE_WR: begin
                act_we_c    = 1'b1;
                act_waddr_c = (cnt[3] ? p2[8:0] : p1[8:0]) + {6'd0, cnt[2:0]};
                act_wstrb_c = 8'hFF;
                for (ei = 0; ei < 4; ei = ei + 1) begin
                    mul_a = ibuf[cnt[3:0]*8 + ei*2] *
                            $signed(rope_cs[0][ei*16 +: 16]) -
                            ibuf[cnt[3:0]*8 + ei*2 + 1] *
                            $signed(rope_cs[1][ei*16 +: 16]) + 48'sd8192;
                    act_wdata_c[ei*16 +: 8] = sat8(mul_a >>> 14);
                    mul_a = ibuf[cnt[3:0]*8 + ei*2] *
                            $signed(rope_cs[1][ei*16 +: 16]) +
                            ibuf[cnt[3:0]*8 + ei*2 + 1] *
                            $signed(rope_cs[0][ei*16 +: 16]) + 48'sd8192;
                    act_wdata_c[ei*16+8 +: 8] = sat8(mul_a >>> 14);
                end
            end
            S_SM_EXP: begin
                if (sm_last) begin
                    act_we_c    = 1'b1;
                    act_waddr_c = AW_PR + {3'd0, p0[8:3]};
                    act_wstrb_c = 8'hFF;
                    for (ei = 0; ei < 8; ei = ei + 1) begin
                        if (ei < cnt_lane)
                            act_wdata_c[ei*8 +: 8] = ppack[ei*8 +: 8];
                        else if (ei == cnt_lane)
                            act_wdata_c[ei*8 +: 8] = pp_val0;
                        else if ((ei == cnt_lane + 32'd1) && sm_two)
                            act_wdata_c[ei*8 +: 8] = pp_val1;
                        else
                            act_wdata_c[ei*8 +: 8] = 8'd0;
                    end
                end else if (cnt[2:0] == 3'd6) begin
                    act_we_c    = 1'b1;
                    act_waddr_c = AW_PR + {3'd0, cnt[8:3]};
                    act_wstrb_c = 8'hFF;
                    act_wdata_c = {pp_val1, pp_val0, ppack[47:0]};
                end
            end
            S_GLU: begin
                if (sub) begin
                    act_we_c    = 1'b1;
                    act_waddr_c = p2[8:0] + {4'd0, cnt[4:0]};
                    act_wstrb_c = 8'hFF;
                    for (ei = 0; ei < 8; ei = ei + 1) begin
                        x_lane = $signed(kreg[ei*8 +: 8]);
                        if (x_lane[7])
                            g_lane = 16'd32767 - sig_tab[abs8(x_lane)];
                        else
                            g_lane = sig_tab[abs8(x_lane)];
                        mul_a = x_lane * g_lane;
                        mul_t = (mul_a + 48'sd16384) >>> 15;
                        mul_w = mul_t * $signed(act_rdata_i[ei*8 +: 8]) + 48'sd64;
                        act_wdata_c[ei*8 +: 8] = sat8(mul_w >>> 7);
                    end
                end
            end
            S_RES: begin
                if (sub) begin
                    act_we_c    = 1'b1;
                    act_waddr_c = p0[8:0] + {6'd0, cnt[2:0]};
                    act_wstrb_c = 8'hFF;
                    for (ei = 0; ei < 8; ei = ei + 1)
                        act_wdata_c[ei*8 +: 8] =
                            sat8({{40{kreg[ei*8+7]}}, kreg[ei*8 +: 8]} +
                                 {{40{act_rdata_i[ei*8+7]}},
                                  act_rdata_i[ei*8 +: 8]});
                end
            end
            default: ;
        endcase

        // K/V quant packs are computed unconditionally from kreg/vreg;
        // both registers are stable through the whole append chain.
        ap_max = max8abs(kreg);
        ap_msb = msb7(ap_max);
        ap_sh  = (ap_msb >= 3'd3) ? {1'b0, ap_msb} - 4'd2 : 4'd0;
        ks16_c = qscale(ap_sh);
        for (ei = 0; ei < 8; ei = ei + 1)
            kpack_c[ei*4 +: 4] = nib4_round($signed(kreg[ei*8 +: 8]), ap_sh);

        ap_max = max8abs(vreg);
        ap_msb = msb7(ap_max);
        ap_sh  = (ap_msb >= 3'd3) ? {1'b0, ap_msb} - 4'd2 : 4'd0;
        vs16_c = qscale(ap_sh);
        for (ei = 0; ei < 8; ei = ei + 1)
            vpack_c[ei*4 +: 4] = nib4_round($signed(vreg[ei*8 +: 8]), ap_sh);
    end

    // ------------------------------------------------------------------
    // Main FSM (registers only; datapath is the combinational block above)
    // ------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= S_IDLE;
            ret_state   <= S_IDLE;
            p0          <= 12'd0;
            p1          <= 12'd0;
            p2          <= 9'd0;
            cnt         <= 16'd0;
            sub         <= 1'b0;
            busy_o      <= 1'b0;
            done_o      <= 1'b0;
            vec_we_o    <= 1'b0;
            kv_we_o     <= 1'b0;
            sumsq       <= 32'd0;
            inv_rms     <= 16'd0;
            smax        <= 32'sd0;
            sum_exp     <= 32'd0;
            sq_rem      <= 19'd0;
            sq_val      <= 32'd0;
            sq_root     <= 16'd0;
            sq_cnt      <= 5'd0;
            dv_num      <= 32'd0;
            dv_den      <= 16'd0;
            dv_rem      <= 15'd0;
            dv_quo      <= 27'd0;
            dv_cnt      <= 6'd0;
            hcnt        <= 4'd0;
            kreg        <= 64'd0;
            vreg        <= 64'd0;
            ppack       <= 64'd0;
            emb_scale   <= 16'd0;
            vec_waddr_o <= 10'd0;
            vec_wdata_o <= 64'd0;
            kv_waddr_o  <= 12'd0;
            kv_wdata_o  <= 256'd0;
            kv_wstrb_o  <= 32'd0;
        end else if (soft_reset_i) begin
            state       <= S_IDLE;
            busy_o      <= 1'b0;
            done_o      <= 1'b0;
            vec_we_o    <= 1'b0;
            kv_we_o     <= 1'b0;
        end else begin
            vec_we_o <= 1'b0;
            kv_we_o  <= 1'b0;
            done_o   <= 1'b0;

            case (state)
                // --------------------------------------------------
                S_IDLE: begin
                    busy_o <= 1'b0;
                    if (start_i) begin
                        p0     <= p0_i;
                        p1     <= p1_i;
                        p2     <= p2_i;
                        cnt    <= 16'd0;
                        sub    <= 1'b0;
                        busy_o <= 1'b1;
                        case (op_i)
                            OP_EMBED:    state <= S_EMB_SC;
                            OP_RMSNORM:  begin
                                state <= S_RMS_RD;
                                sumsq <= 32'd0;
                            end
                            OP_ROPE:     state <= S_ROPE_TAB;
                            OP_SOFTMAX:  begin
                                state   <= S_SM_SC;
                                smax    <= 32'h8000_0000;
                                sum_exp <= 32'd0;
                            end
                            OP_SWIGLU:   state <= S_GLU;
                            OP_RESADD:   state <= S_RES;
                            OP_KVAPPEND: begin
                                state <= S_KVA_RD;
                                hcnt  <= 4'd0;
                            end
                            default: state <= S_DONE;
                        endcase
                    end
                end

                // ---------------- EMBED ----------------
                S_EMB_SC: begin
                    // scale word combinationally addressed this cycle
                    if (p0[3])
                        emb_scale <= wbuf_rdata_i[128 + p0[2:0]*16 +: 16];
                    else
                        emb_scale <= wbuf_rdata_i[p0[2:0]*16 +: 16];
                    state <= S_EMB_RD;
                    cnt   <= 16'd0;
                end

                S_EMB_RD: begin
                    if (cnt == 16'd7) state <= S_DONE;
                    else              cnt   <= cnt + 16'd1;
                end

                // ---------------- RMSNORM ----------------
                S_RMS_RD: begin
                    for (ei = 0; ei < 8; ei = ei + 1)
                        ibuf[cnt[2:0]*8 + ei] <= act_rdata_i[ei*8 +: 8];
                    sumsq <= sumsq + sq8(act_rdata_i);
                    if (cnt == 16'd7) begin
                        sq_val   <= sumsq + sq8(act_rdata_i);
                        sq_rem   <= 19'd0;
                        sq_root  <= 16'd0;
                        sq_cnt   <= 5'd0;
                        ret_state <= S_RMS_DIV;
                        state    <= S_SQRT;
                        cnt      <= 16'd0;
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end

                S_SQRT: begin
                    // 4 restoring iterations per cycle: 16/4 = 4 cycles
                    sq_rem  <= s4_remo;
                    sq_root <= s4_root;
                    sq_val  <= {s3_val[29:0], 2'b00};
                    if (sq_cnt == 5'd3) begin
                        sq_cnt <= 5'd0;
                        if (ret_state == S_RMS_DIV) begin
                            dv_num <= 32'd131072;
                            dv_den <= (s4_root == 16'd0) ? 16'd1 : s4_root;
                            dv_rem <= 15'd0;
                            dv_quo <= 27'd0;
                            dv_cnt <= 6'd0;
                            ret_state <= S_RMS_GAIN;
                            state     <= S_DIV;
                        end else begin
                            state <= ret_state;
                        end
                    end else begin
                        sq_cnt <= sq_cnt + 5'd1;
                    end
                end

                S_DIV: begin
                    // 2 restoring iterations per cycle: 32/2 = 16 cycles
                    // (32 iterations are required for the exact quotient;
                    // 26 iterations would return quotient >> 6)
                    dv_rem <= d2_remo;
                    dv_num <= {d1_num[30:0], 1'b0};
                    dv_quo <= {dv_quo[24:0], d1_take, d2_take};
                    if (dv_cnt == 6'd15) begin
                        dv_cnt <= 6'd0;
                        state  <= ret_state;
                    end else begin
                        dv_cnt <= dv_cnt + 6'd1;
                    end
                end

                S_RMS_DIV: begin
                    // unreachable placeholder (div is entered from sqrt)
                    state <= S_RMS_GAIN;
                end

                S_RMS_GAIN: begin
                    if (cnt == 16'd0)
                        inv_rms <= (dv_quo > 27'd16383) ? 16'd16383 : dv_quo[15:0];
                    for (ei = 0; ei < 4; ei = ei + 1)
                        gbuf[cnt[3:0]*4 + ei] <= vec_rdata_i[ei*16 +: 16];
                    if (cnt == 16'd15) begin
                        cnt   <= 16'd0;
                        state <= S_RMS_WR;
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end

                S_RMS_WR: begin
                    if (cnt == 16'd7) state <= S_DONE;
                    else              cnt   <= cnt + 16'd1;
                end

                // ---------------- ROPE ----------------
                S_ROPE_TAB: begin
                    if (p0[0]) begin
                        rope_cs[0] <= wbuf_rdata_i[191:128];
                        rope_cs[1] <= wbuf_rdata_i[255:192];
                    end else begin
                        rope_cs[0] <= wbuf_rdata_i[63:0];
                        rope_cs[1] <= wbuf_rdata_i[127:64];
                    end
                    cnt   <= 16'd0;
                    state <= S_ROPE_RD;
                end

                S_ROPE_RD: begin
                    for (ei = 0; ei < 8; ei = ei + 1)
                        ibuf[cnt[3:0]*8 + ei] <= act_rdata_i[ei*8 +: 8];
                    if (cnt == 16'd11) begin
                        cnt   <= 16'd0;
                        state <= S_ROPE_WR;
                    end else begin
                        cnt <= cnt + 16'd1;
                    end
                end

                S_ROPE_WR: begin
                    if (cnt == 16'd11) state <= S_DONE;
                    else               cnt   <= cnt + 16'd1;
                end

                // ---------------- SOFTMAX ----------------
                S_SM_SC: begin
                    // two positions per cycle (they share one ACT word and
                    // one scale word because cnt stays even)
                    sbuf[cnt[8:0]]         <= sc_val0;
                    sbuf[cnt[8:0] + 9'd1]  <= sm_two ? sc_val1 : sc_val0;
                    if (cnt == 16'd0)
                        smax <= sm_two ? sc_best : sc_val0;
                    else if (sm_two ? (sc_best > smax) : (sc_val0 > smax))
                        smax <= sm_two ? sc_best : sc_val0;
                    if (sm_last) begin
                        cnt   <= 16'd0;
                        state <= S_SM_EXP;
                    end else begin
                        cnt <= cnt + 16'd2;
                    end
                end

                S_SM_EXP: begin
                    sum_exp <= sum_exp_next;
                    ppack[cnt[2:0]*8 +: 8]      <= pp_val0;
                    ppack[cnt[2:0]*8 + 8 +: 8]  <= sm_two ? pp_val1 : 8'd0;
                    if (sm_last) begin
                        dv_num <= 32'd268435456; // 2^28: att lands on x8 grid
                        dv_den <= (sum_exp_next[15:0] == 16'd0) ? 16'd1
                                                              : sum_exp_next[15:0];
                        dv_rem <= 15'd0;
                        dv_quo <= 27'd0;
                        dv_cnt <= 6'd0;
                        ret_state <= S_SM_RQ;
                        state     <= S_DIV;
                        cnt       <= 16'd0;
                    end else begin
                        cnt <= cnt + 16'd2;
                    end
                end

                S_SM_DIV: state <= S_SM_RQ; // placeholder

                S_SM_RQ: begin
                    vec_we_o    <= 1'b1;
                    vec_waddr_o <= VW_RQ + RQ_ATT_SLOT;
                    vec_wdata_o <= {24'd0, 8'd22, 6'd0, dv_quo[25:0]};
                    state       <= S_DONE;
                end

                // ---------------- SWIGLU ----------------
                S_GLU: begin
                    if (!sub) begin
                        kreg        <= act_rdata_i;
                        sub         <= 1'b1;
                    end else begin
                        sub <= 1'b0;
                        if (cnt == 16'd21) state <= S_DONE;
                        else               cnt   <= cnt + 16'd1;
                    end
                end

                // ---------------- RESADD ----------------
                S_RES: begin
                    if (!sub) begin
                        kreg        <= act_rdata_i;
                        sub         <= 1'b1;
                    end else begin
                        sub <= 1'b0;
                        if (cnt == 16'd7) state <= S_DONE;
                        else              cnt   <= cnt + 16'd1;
                    end
                end

                // ---------------- KVAPPEND ----------------
                S_KVA_RD: begin
                    if (!sub) begin
                        kreg        <= act_rdata_i;
                        sub         <= 1'b1;
                    end else begin
                        vreg        <= act_rdata_i;
                        sub         <= 1'b0;
                        state       <= S_KVA_KW;
                    end
                end

                S_KVA_KW: begin
                    kv_we_o    <= 1'b1;
                    kv_waddr_o <= p1[11:0] + h64 + {6'd0, p0[8:3]};
                    kv_wdata_o <= {8{kpack_c}};
                    kv_wstrb_o <= 32'h0000_000F << {p0[2:0], 2'b00};
                    state      <= S_KVA_KSW;
                end

                S_KVA_KSW: begin
                    kv_we_o    <= 1'b1;
                    kv_waddr_o <= p1[11:0] + KV_KSC_OFF + h32 + {7'd0, p0[8:4]};
                    kv_wdata_o <= {16{ks16_c}};
                    kv_wstrb_o <= 32'h0000_0003 << {p0[3:0], 1'b0};
                    state      <= S_KVA_VW;
                end

                S_KVA_VW: begin
                    kv_we_o    <= 1'b1;
                    kv_waddr_o <= p1[11:0] + KV_V_OFF + h64 + {6'd0, p0[8:3]};
                    kv_wdata_o <= {8{vpack_c}};
                    kv_wstrb_o <= 32'h0000_000F << {p0[2:0], 2'b00};
                    state      <= S_KVA_VSW;
                end

                S_KVA_VSW: begin
                    kv_we_o    <= 1'b1;
                    kv_waddr_o <= p1[11:0] + KV_VSC_OFF + h32 + {7'd0, p0[8:4]};
                    kv_wdata_o <= {16{vs16_c}};
                    kv_wstrb_o <= 32'h0000_0003 << {p0[3:0], 1'b0};
                    if (hcnt == 4'd3) begin
                        state <= S_DONE;
                    end else begin
                        hcnt  <= hcnt + 4'd1;
                        state <= S_KVA_RD;
                    end
                end

                // ---------------- DONE ----------------
                S_DONE: begin
                    done_o <= 1'b1;
                    busy_o <= 1'b0;
                    state  <= S_IDLE;
                end

                default: state <= S_IDLE;
            endcase
        end
    end

endmodule
