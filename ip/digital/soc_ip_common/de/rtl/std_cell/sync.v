// Module   : sync
// Function : Multi-bit multi-stage synchronizer for crg-gen.
//            Parameters D_WIDTH / DATA_DEFAULT match generator instances.

module sync #(
    parameter D_WIDTH      = 1,
    parameter DATA_DEFAULT = {D_WIDTH{1'b0}}
) (
    input  wire                 clk_d,
    input  wire                 rst_d_n,
    input  wire [D_WIDTH-1:0]   data_s,
    output wire [D_WIDTH-1:0]   data_d
);

    genvar i;
    generate
        for (i = 0; i < D_WIDTH; i = i + 1) begin : g_bit
            // Per-bit 2-stage sync; default value applied on reset.
            reg s0, s1;
            always @(posedge clk_d or negedge rst_d_n) begin
                if (!rst_d_n) begin
                    s0 <= DATA_DEFAULT[i];
                    s1 <= DATA_DEFAULT[i];
                end else begin
                    s0 <= data_s[i];
                    s1 <= s0;
                end
            end
            assign data_d[i] = s1;
        end
    endgenerate

endmodule
