//============================================================================
// Module     : stories260k_attn
// Function   : Fused 8-position tiled GQA attention engine
//
// Pass 1 reads K data and K scales in parallel and finds the scaled-score
// maximum. Pass 2 recomputes the scores/exp values, then accumulates the V
// product on the following beat. Scores and probabilities never spill to
// ACTBUF. The arithmetic is bit-exact with docs/design_spec.md.
//============================================================================

module stories260k_attn (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         soft_reset_i,
    input  wire         start_i,
    input  wire [8:0]   pos_i,
    input  wire [11:0]  layer_base_i,
    input  wire [1:0]   kv_head_i,
    input  wire [2:0]   q_head_i,
    input  wire [3:0]   sm_shift_i,
    output reg          busy_o,
    output reg          done_o,
    output reg  [6:0]   mac_adv_o,

    output wire [8:0]   act_raddr_o,
    input  wire [63:0]  act_rdata_i,
    output wire         act_we_o,
    output wire [8:0]   act_waddr_o,
    output wire [63:0]  act_wdata_o,
    output wire [7:0]   act_wstrb_o,

    output wire [11:0]  kv_raddr_o,
    input  wire [255:0] kv_rdata_i,
    output wire [11:0]  kv_scale_raddr_o,
    input  wire [255:0] kv_scale_rdata_i
);

    localparam [8:0] AW_Q   = 9'd16;
    localparam [8:0] AW_ATT = 9'd360;

    localparam [11:0] KV_KSC_OFF = 12'd256;
    localparam [11:0] KV_V_OFF   = 12'd384;
    localparam [11:0] KV_VSC_OFF = 12'd640;

    localparam [3:0] A_IDLE  = 4'd0;
    localparam [3:0] A_QLOAD = 4'd1;
    localparam [3:0] A_MAX   = 4'd2;
    localparam [3:0] A_EXP   = 4'd3;
    localparam [3:0] A_V     = 4'd4;
    localparam [3:0] A_DIV   = 4'd5;
    localparam [3:0] A_WRITE = 4'd6;
    localparam [3:0] A_DONE  = 4'd7;

    reg [3:0]  state;
    reg [8:0]  pos;
    reg [11:0] layer_base;
    reg [1:0]  kv_head;
    reg [2:0]  q_head;
    reg [3:0]  sm_shift;
    reg [5:0]  tile;
    reg [63:0] qreg;

    reg signed [31:0] smax;
    reg        [31:0] sum_exp;
    reg        [7:0]  exp_lane [0:7];
    reg signed [31:0] av_acc [0:7];

    // 2-bit/cycle restoring divider, identical to the SFU divider.
    reg [31:0] dv_num;
    reg [15:0] dv_den;
    reg [14:0] dv_rem;
    reg [26:0] dv_quo;
    reg [4:0]  dv_cnt;

    wire [15:0] d1_rem   = {dv_rem, dv_num[31]};
    wire        d1_take  = (d1_rem >= dv_den);
    wire [15:0] d1_rdif  = d1_rem - dv_den;
    wire [14:0] d1_remo  = d1_take ? d1_rdif[14:0] : d1_rem[14:0];
    wire [31:0] d1_num   = {dv_num[30:0], 1'b0};
    wire [15:0] d2_rem   = {d1_remo, d1_num[31]};
    wire        d2_take  = (d2_rem >= dv_den);
    wire [15:0] d2_rdif  = d2_rem - dv_den;
    wire [14:0] d2_remo  = d2_take ? d2_rdif[14:0] : d2_rem[14:0];
    wire [1:0]  unused_dv_carry = {d1_rdif[15], d2_rdif[15]};

    wire [11:0] kvh64 = {4'd0, kv_head, 6'b000000};
    wire [11:0] kvh32 = {5'd0, kv_head, 5'b00000};
    wire [5:0]  last_tile = pos[8:3];
    wire [9:0]  tile_pos0 = {1'b0, tile, 3'b000};

    assign act_raddr_o = AW_Q + {6'd0, q_head};
    assign act_waddr_o = AW_ATT + {6'd0, q_head};
    assign act_wstrb_o = 8'hFF;
    assign act_we_o    = (state == A_WRITE);

    assign kv_raddr_o = layer_base + kvh64 + {6'd0, tile} +
                        ((state == A_V) ? KV_V_OFF : 12'd0);
    assign kv_scale_raddr_o = layer_base + kvh32 + {7'd0, tile[5:1]} +
                              ((state == A_V) ? KV_VSC_OFF : KV_KSC_OFF);

    // Q0.7 exp LUT, index is the clamped Q4-domain delta plus 128.
    reg [7:0] exp_tab [0:128];
    initial begin
        exp_tab[0]=0; exp_tab[1]=0; exp_tab[2]=0; exp_tab[3]=0;
        exp_tab[4]=0; exp_tab[5]=0; exp_tab[6]=0; exp_tab[7]=0;
        exp_tab[8]=0; exp_tab[9]=0; exp_tab[10]=0; exp_tab[11]=0;
        exp_tab[12]=0; exp_tab[13]=0; exp_tab[14]=0; exp_tab[15]=0;
        exp_tab[16]=0; exp_tab[17]=0; exp_tab[18]=0; exp_tab[19]=0;
        exp_tab[20]=0; exp_tab[21]=0; exp_tab[22]=0; exp_tab[23]=0;
        exp_tab[24]=0; exp_tab[25]=0; exp_tab[26]=0; exp_tab[27]=0;
        exp_tab[28]=0; exp_tab[29]=0; exp_tab[30]=0; exp_tab[31]=0;
        exp_tab[32]=0; exp_tab[33]=0; exp_tab[34]=0; exp_tab[35]=0;
        exp_tab[36]=0; exp_tab[37]=0; exp_tab[38]=0; exp_tab[39]=0;
        exp_tab[40]=1; exp_tab[41]=1; exp_tab[42]=1; exp_tab[43]=1;
        exp_tab[44]=1; exp_tab[45]=1; exp_tab[46]=1; exp_tab[47]=1;
        exp_tab[48]=1; exp_tab[49]=1; exp_tab[50]=1; exp_tab[51]=1;
        exp_tab[52]=1; exp_tab[53]=1; exp_tab[54]=1; exp_tab[55]=1;
        exp_tab[56]=1; exp_tab[57]=2; exp_tab[58]=2; exp_tab[59]=2;
        exp_tab[60]=2; exp_tab[61]=2; exp_tab[62]=2; exp_tab[63]=2;
        exp_tab[64]=2; exp_tab[65]=2; exp_tab[66]=3; exp_tab[67]=3;
        exp_tab[68]=3; exp_tab[69]=3; exp_tab[70]=3; exp_tab[71]=4;
        exp_tab[72]=4; exp_tab[73]=4; exp_tab[74]=4; exp_tab[75]=5;
        exp_tab[76]=5; exp_tab[77]=5; exp_tab[78]=6; exp_tab[79]=6;
        exp_tab[80]=6; exp_tab[81]=7; exp_tab[82]=7; exp_tab[83]=8;
        exp_tab[84]=8; exp_tab[85]=9; exp_tab[86]=9; exp_tab[87]=10;
        exp_tab[88]=10; exp_tab[89]=11; exp_tab[90]=12; exp_tab[91]=13;
        exp_tab[92]=13; exp_tab[93]=14; exp_tab[94]=15; exp_tab[95]=16;
        exp_tab[96]=17; exp_tab[97]=18; exp_tab[98]=19; exp_tab[99]=21;
        exp_tab[100]=22; exp_tab[101]=23; exp_tab[102]=25; exp_tab[103]=27;
        exp_tab[104]=28; exp_tab[105]=30; exp_tab[106]=32; exp_tab[107]=34;
        exp_tab[108]=36; exp_tab[109]=39; exp_tab[110]=41; exp_tab[111]=44;
        exp_tab[112]=47; exp_tab[113]=50; exp_tab[114]=53; exp_tab[115]=56;
        exp_tab[116]=60; exp_tab[117]=64; exp_tab[118]=68; exp_tab[119]=72;
        exp_tab[120]=77; exp_tab[121]=82; exp_tab[122]=87; exp_tab[123]=93;
        exp_tab[124]=99; exp_tab[125]=105; exp_tab[126]=112; exp_tab[127]=119;
        exp_tab[128]=127;
    end

    integer i, j;
    integer dot_tmp;
    reg signed [31:0] score_lane [0:7];
    reg signed [31:0] scaled_lane [0:7];
    reg signed [31:0] tile_max;
    reg signed [47:0] scale_prod;
    reg signed [31:0] z_full;
    reg signed [7:0]  z_clamp;
    reg        [7:0]  exp_comb [0:7];
    reg        [31:0] exp_sum_comb;
    reg        [7:0]  pp_comb [0:7];
    reg signed [31:0] v_add [0:7];
    reg signed [7:0]  q_lane;
    reg signed [7:0]  k_lane;
    reg signed [7:0]  v_lane;
    // Separate temps: shared scale_lane was multi-driven by the K-score and
    // V-product comb blocks (Yosys rtlil assert / X risk in some flows).
    reg        [15:0] k_scale_lane;
    reg        [15:0] v_scale_lane;
    reg        [23:0] pp_prod;
    reg        [23:0] pp_round;
    reg        [9:0]  lane_pos;
    reg        [15:0] unused_scale_bits;
    reg        [15:0] unused_pp_bits;

    // K-side tile computation. Invalid tail lanes are completely masked.
    always @* begin
        tile_max    = 32'h8000_0000;
        exp_sum_comb = 32'd0;
        q_lane      = 8'sd0;
        k_lane      = 8'sd0;
        k_scale_lane = 16'd0;
        scale_prod  = 48'sd0;
        z_full      = 32'sd0;
        z_clamp     = 8'sd0;
        lane_pos    = 10'd0;
        unused_scale_bits = 16'd0;
        for (i = 0; i < 8; i = i + 1) begin
            if (i == 0) lane_pos = tile_pos0;
            dot_tmp = 0;
            for (j = 0; j < 8; j = j + 1) begin
                q_lane = $signed(qreg[j*8 +: 8]);
                k_lane = $signed({{4{kv_rdata_i[i*32+j*4+3]}},
                                  kv_rdata_i[i*32+j*4 +: 4]});
                dot_tmp = dot_tmp + q_lane * k_lane;
            end
            score_lane[i] = dot_tmp;
            k_scale_lane = kv_scale_rdata_i[(tile[0]*8+i)*16 +: 16];
            scale_prod = score_lane[i] * $signed({1'b0, k_scale_lane}) + 48'sd1024;
            scaled_lane[i] = $signed(scale_prod[42:11]);
            unused_scale_bits = {scale_prod[47:43], scale_prod[10:0]};
            if ((lane_pos <= {1'b0, pos}) && (scaled_lane[i] > tile_max))
                tile_max = scaled_lane[i];

            z_full = (scaled_lane[i] - smax) >>> sm_shift;
            z_clamp = (z_full < -32'sd128) ? -8'sd128 :
                      (z_full > 32'sd0) ? 8'sd0 : z_full[7:0];
            if (lane_pos <= {1'b0, pos}) begin
                exp_comb[i] = exp_tab[z_clamp + 8'd128];
                exp_sum_comb = exp_sum_comb +
                               {24'd0, exp_tab[z_clamp + 8'd128]};
            end else begin
                exp_comb[i] = 8'd0;
            end
            lane_pos = lane_pos + 10'd1;
        end
    end

    // V-side product. p' rounding and the INT4 V multiply are performed
    // before the local reciprocal, exactly like the former PR + AV path.
    always @* begin
        v_lane    = 8'sd0;
        v_scale_lane = 16'd0;
        pp_prod   = 24'd0;
        pp_round  = 24'd0;
        unused_pp_bits = 16'd0;
        for (i = 0; i < 8; i = i + 1) begin
            v_scale_lane = kv_scale_rdata_i[(tile[0]*8+i)*16 +: 16];
            pp_prod = exp_lane[i] * v_scale_lane;
            pp_round = pp_prod + 24'd16384;
            pp_comb[i] = pp_round[22:15];
            unused_pp_bits = {pp_round[23], pp_round[14:0]};
        end
        for (j = 0; j < 8; j = j + 1) begin
            v_add[j] = 32'sd0;
            for (i = 0; i < 8; i = i + 1) begin
                v_lane = $signed({{4{kv_rdata_i[i*32+j*4+3]}},
                                  kv_rdata_i[i*32+j*4 +: 4]});
                v_add[j] = v_add[j] + $signed({1'b0, pp_comb[i]}) * v_lane;
            end
        end
    end

    reg signed [63:0] out_prod;
    reg signed [63:0] out_shift;
    reg [63:0] out_word;
    always @* begin
        out_word  = 64'd0;
        out_prod  = 64'sd0;
        out_shift = 64'sd0;
        for (j = 0; j < 8; j = j + 1) begin
            out_prod  = av_acc[j] * $signed({1'b0, dv_quo}) + 64'sd2097152;
            out_shift = out_prod >>> 22;
            out_word[j*8 +: 8] = (out_shift > 64'sd127) ? 8'h7f :
                                  (out_shift < -64'sd128) ? 8'h80 : out_shift[7:0];
        end
    end
    assign act_wdata_o = out_word;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= A_IDLE;
            busy_o    <= 1'b0;
            done_o    <= 1'b0;
            mac_adv_o <= 7'd0;
            pos       <= 9'd0;
            layer_base <= 12'd0;
            kv_head   <= 2'd0;
            q_head    <= 3'd0;
            sm_shift  <= 4'd0;
            tile      <= 6'd0;
            qreg      <= 64'd0;
            smax      <= 32'h8000_0000;
            sum_exp   <= 32'd0;
            dv_num    <= 32'd0;
            dv_den    <= 16'd1;
            dv_rem    <= 15'd0;
            dv_quo    <= 27'd0;
            dv_cnt    <= 5'd0;
            for (i = 0; i < 8; i = i + 1) begin
                exp_lane[i] <= 8'd0;
                av_acc[i]   <= 32'sd0;
            end
        end else if (soft_reset_i) begin
            state     <= A_IDLE;
            busy_o    <= 1'b0;
            done_o    <= 1'b0;
            mac_adv_o <= 7'd0;
        end else begin
            done_o    <= 1'b0;
            mac_adv_o <= 7'd0;
            case (state)
                A_IDLE: begin
                    busy_o <= 1'b0;
                    if (start_i) begin
                        pos        <= pos_i;
                        layer_base <= layer_base_i;
                        kv_head    <= kv_head_i;
                        q_head     <= q_head_i;
                        sm_shift   <= sm_shift_i;
                        tile       <= 6'd0;
                        smax       <= 32'h8000_0000;
                        sum_exp    <= 32'd0;
                        for (i = 0; i < 8; i = i + 1)
                            av_acc[i] <= 32'sd0;
                        busy_o <= 1'b1;
                        state  <= A_QLOAD;
                    end
                end
                A_QLOAD: begin
                    qreg  <= act_rdata_i;
                    tile  <= 6'd0;
                    state <= A_MAX;
                end
                A_MAX: begin
                    mac_adv_o <= 7'd64;
                    if ((tile == 6'd0) || (tile_max > smax)) smax <= tile_max;
                    if (tile == last_tile) begin
                        tile    <= 6'd0;
                        sum_exp <= 32'd0;
                        state   <= A_EXP;
                    end else begin
                        tile <= tile + 6'd1;
                    end
                end
                A_EXP: begin
                    mac_adv_o <= 7'd64;
                    for (i = 0; i < 8; i = i + 1)
                        exp_lane[i] <= exp_comb[i];
                    sum_exp <= sum_exp + exp_sum_comb;
                    state   <= A_V;
                end
                A_V: begin
                    mac_adv_o <= 7'd64;
                    for (i = 0; i < 8; i = i + 1)
                        av_acc[i] <= av_acc[i] + v_add[i];
                    if (tile == last_tile) begin
                        dv_num <= 32'd268435456;
                        dv_den <= (sum_exp[15:0] == 16'd0) ? 16'd1 : sum_exp[15:0];
                        dv_rem <= 15'd0;
                        dv_quo <= 27'd0;
                        dv_cnt <= 5'd0;
                        state  <= A_DIV;
                    end else begin
                        tile  <= tile + 6'd1;
                        state <= A_EXP;
                    end
                end
                A_DIV: begin
                    dv_rem <= d2_remo;
                    dv_num <= {d1_num[30:0], 1'b0};
                    dv_quo <= {dv_quo[24:0], d1_take, d2_take};
                    if (dv_cnt == 5'd15) begin
                        dv_cnt <= 5'd0;
                        state  <= A_WRITE;
                    end else begin
                        dv_cnt <= dv_cnt + 5'd1;
                    end
                end
                A_WRITE: state <= A_DONE;
                A_DONE: begin
                    done_o <= 1'b1;
                    busy_o <= 1'b0;
                    state  <= A_IDLE;
                end
                default: state <= A_IDLE;
            endcase
        end
    end

endmodule
