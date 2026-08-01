//============================================================================
// Module     : npu_mac
// Function   : Four-lane signed INT8 multiply-accumulate
//============================================================================

module npu_mac (
    input  signed [31:0] acc_i,
    input  signed [7:0]  act0_i,
    input  signed [7:0]  act1_i,
    input  signed [7:0]  act2_i,
    input  signed [7:0]  act3_i,
    input  signed [7:0]  wgt0_i,
    input  signed [7:0]  wgt1_i,
    input  signed [7:0]  wgt2_i,
    input  signed [7:0]  wgt3_i,
    output signed [31:0] acc_o
);

    wire signed [15:0] prod0;
    wire signed [15:0] prod1;
    wire signed [15:0] prod2;
    wire signed [15:0] prod3;
    wire signed [16:0] prod0_ext;
    wire signed [16:0] prod1_ext;
    wire signed [16:0] prod2_ext;
    wire signed [16:0] prod3_ext;
    wire signed [16:0] prod_sum01;
    wire signed [16:0] prod_sum23;
    wire signed [17:0] prod_sum;
    wire signed [31:0] prod_sum_ext;

    assign prod0 = act0_i * wgt0_i;
    assign prod1 = act1_i * wgt1_i;
    assign prod2 = act2_i * wgt2_i;
    assign prod3 = act3_i * wgt3_i;

    assign prod0_ext = {prod0[15], prod0};
    assign prod1_ext = {prod1[15], prod1};
    assign prod2_ext = {prod2[15], prod2};
    assign prod3_ext = {prod3[15], prod3};

    // Preserve the exact four-product sum before the final modulo-2^32 add.
    assign prod_sum01 = prod0_ext + prod1_ext;
    assign prod_sum23 = prod2_ext + prod3_ext;
    assign prod_sum = {{1{prod_sum01[16]}}, prod_sum01} +
                      {{1{prod_sum23[16]}}, prod_sum23};
    assign prod_sum_ext = {{14{prod_sum[17]}}, prod_sum};

    assign acc_o = acc_i + prod_sum_ext;

endmodule
