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

    assign prod0 = act0_i * wgt0_i;
    assign prod1 = act1_i * wgt1_i;
    assign prod2 = act2_i * wgt2_i;
    assign prod3 = act3_i * wgt3_i;

    assign acc_o = acc_i +
                   {{16{prod0[15]}}, prod0} +
                   {{16{prod1[15]}}, prod1} +
                   {{16{prod2[15]}}, prod2} +
                   {{16{prod3[15]}}, prod3};

endmodule
