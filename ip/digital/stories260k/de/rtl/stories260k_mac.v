//============================================================================
// Module     : stories260k_mac
// Function   : 8x8 INT4/INT8 MAC array with fused per-group dequantization
//
// Eight rows x eight lanes of signed 8x8 multiply per cycle. INT4 weights are
// sign-extended to 8 bits by the unpack logic upstream, so the same array also
// serves INT8 KV-cache tiles. Dequantization is fused: each row keeps a group
// partial sum; on the group boundary (grp_last_i) the partial sum is
// multiplied by that row's Q4.12 scale and folded into the INT32 main
// accumulator, so no separate dequantized weight tensor ever exists.
//============================================================================

module stories260k_mac (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         acc_clear_i,   // clear main + partial accumulators
    input  wire         en_i,          // accumulate this cycle
    input  wire         grp_last_i,    // last cycle of current scale group
    input  wire         scale_en_i,    // 0: force scale = 1.0 (Q4.12)
    input  wire [511:0] w_flat_i,      // 8 rows x 8 lanes x int8
    input  wire [63:0]  x_flat_i,      // 8 lanes x int8 (row broadcast)
    input  wire [127:0] scale_flat_i,  // 8 rows x int16 Q4.12
    output wire [255:0] acc_flat_o     // 8 rows x int32 main accumulators
);

    genvar r;

    generate
        for (r = 0; r < 8; r = r + 1) begin : g_row
            wire signed [7:0] x0 = x_flat_i[7:0];
            wire signed [7:0] x1 = x_flat_i[15:8];
            wire signed [7:0] x2 = x_flat_i[23:16];
            wire signed [7:0] x3 = x_flat_i[31:24];
            wire signed [7:0] x4 = x_flat_i[39:32];
            wire signed [7:0] x5 = x_flat_i[47:40];
            wire signed [7:0] x6 = x_flat_i[55:48];
            wire signed [7:0] x7 = x_flat_i[63:56];

            wire signed [7:0] w0 = w_flat_i[r*64+7 : r*64];
            wire signed [7:0] w1 = w_flat_i[r*64+15 : r*64+8];
            wire signed [7:0] w2 = w_flat_i[r*64+23 : r*64+16];
            wire signed [7:0] w3 = w_flat_i[r*64+31 : r*64+24];
            wire signed [7:0] w4 = w_flat_i[r*64+39 : r*64+32];
            wire signed [7:0] w5 = w_flat_i[r*64+47 : r*64+40];
            wire signed [7:0] w6 = w_flat_i[r*64+55 : r*64+48];
            wire signed [7:0] w7 = w_flat_i[r*64+63 : r*64+56];

            // 8 products of |127*127| max; sum fits in signed 21 bits.
            wire signed [20:0] dotsum =
                w0*x0 + w1*x1 + w2*x2 + w3*x3 +
                w4*x4 + w5*x5 + w6*x6 + w7*x7;

            reg signed [24:0] part_acc;
            reg signed [31:0] main_acc;

            wire signed [24:0] part_next = part_acc +
                                             {{4{dotsum[20]}}, dotsum};

            wire signed [15:0] scale =
                scale_en_i ? scale_flat_i[r*16+15 : r*16] : 16'sh1000;

            // Q4.12 dequant: (part * scale + 2^11) >>> 12, round-half-up
            wire signed [40:0] scaled     = part_next * scale;
            wire signed [40:0] scaled_r   = scaled + 41'sd2048;
            wire signed [31:0] group_val  = {{3{scaled_r[40]}}, scaled_r[40:12]};
            // low 12 product bits are folded by the rounding shift
            wire [11:0] unused_scaled_lo  = scaled_r[11:0];

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    part_acc <= 25'sd0;
                    main_acc <= 32'sd0;
                end else if (acc_clear_i) begin
                    part_acc <= 25'sd0;
                    main_acc <= 32'sd0;
                end else if (en_i) begin
                    if (grp_last_i) begin
                        main_acc <= main_acc + group_val;
                        part_acc <= 25'sd0;
                    end else begin
                        part_acc <= part_next;
                    end
                end
            end

            assign acc_flat_o[r*32+31 : r*32] = main_acc;
        end
    endgenerate

endmodule
