//============================================================================
// Module     : npu_requant
// Function   : INT32 bias result requantization, activation, and INT8 cast
//============================================================================

module npu_requant (
    input  signed [31:0] post_bias_i,
    input  signed [31:0] quant_mult_i,
    input         [5:0]  quant_shift_i,
    input  signed [7:0]  out_zero_point_i,
    input         [1:0]  activation_mode_i,
    input  signed [7:0]  relu6_max_i,
    output reg    [7:0]  out_byte_o,
    output reg           sat_clip_o
);

    localparam ACT_RELU  = 2'd1;
    localparam ACT_RELU6 = 2'd2;

    reg signed [63:0] product;
    reg signed [63:0] rounded;
    reg signed [63:0] shifted;
    reg signed [63:0] with_zp;
    reg signed [63:0] activated;
    reg signed [63:0] round_add;
    reg signed [63:0] zp_ext;
    reg signed [63:0] relu6_ext;
    always @* begin
        product = $signed(post_bias_i) * $signed(quant_mult_i);
        rounded = 64'sd0;
        round_add = 64'sd0;

        if (quant_shift_i == 6'd0) begin
            shifted = product;
        end else begin
            round_add = 64'sd1 <<< (quant_shift_i - 6'd1);
            rounded   = product + round_add;
            shifted   = rounded >>> quant_shift_i;
        end

        zp_ext    = {{56{out_zero_point_i[7]}}, out_zero_point_i};
        relu6_ext = {{56{relu6_max_i[7]}}, relu6_max_i};
        with_zp   = shifted + zp_ext;
        activated = with_zp;

        if (activation_mode_i == ACT_RELU) begin
            if (activated < zp_ext) begin
                activated = zp_ext;
            end
        end else if (activation_mode_i == ACT_RELU6) begin
            if (activated < zp_ext) begin
                activated = zp_ext;
            end
            if (activated > relu6_ext) begin
                activated = relu6_ext;
            end
        end

        if (!activated[63] && (|activated[62:7])) begin
            out_byte_o = 8'h7f;
            sat_clip_o = 1'b1;
        end else if (activated[63] && !(&activated[62:7])) begin
            out_byte_o = 8'h80;
            sat_clip_o = 1'b1;
        end else begin
            out_byte_o = activated[7:0];
            sat_clip_o = 1'b0;
        end
    end

endmodule
