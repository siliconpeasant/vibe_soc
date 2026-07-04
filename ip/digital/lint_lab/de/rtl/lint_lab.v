// lint_lab - intentional SpyGlass lint benchmark corpus.
// This RTL is deliberately bad. Do not reuse it as product logic.

`timescale 1ns / 1ps

module lint_lab (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,
    input  wire [7:0]  data_in,
    output wire [7:0]  data_out,
    output wire        valid_out
);
    wire [7:0] undriven_bus;
    wire [7:0] case_y;
    wire       seq_q;
    wire       comb_y;
    wire       reset_q;
    wire       edge_q;
    wire       loop_y;
    wire       prim_y;
    wire       self_y;
    wire       loop_a;
    wire       loop_b;
    wire       multi_driver;
    wire       unconnected_y;
    wire       expr_y;
    wire       unused_top_wire;
    wire       extra_expr_y;
    wire [1:0] div_y;

    assign multi_driver = en;
    assign multi_driver = rst_n;
    assign loop_a = ~loop_b;
    assign loop_b = loop_a;
    assign data_out = undriven_bus ^ case_y;
    assign div_y = data_in[1:0] / data_in[3:2];
    assign valid_out = seq_q | comb_y | reset_q | edge_q | loop_y | prim_y | self_y | expr_y | extra_expr_y | multi_driver | div_y[0];

    lint_lab_bad_seq u_bad_seq (
        .clk(clk),
        .rst_n(rst_n),
        .d(data_in[0]),
        .q(seq_q)
    );

    lint_lab_bad_comb u_bad_comb (
        .a(data_in[1]),
        .b(data_in[2]),
        .sel(en),
        .y(comb_y)
    );

    lint_lab_bad_case u_bad_case (
        .sel(data_in[2:0]),
        .a(data_in),
        .y(case_y)
    );

    lint_lab_bad_reset u_bad_reset (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .d(data_in[3]),
        .q(reset_q)
    );

    lint_lab_both_edges u_both_edges (
        .clk(clk),
        .d(data_in[4]),
        .q(edge_q)
    );

    lint_lab_loop_bad u_loop_bad (
        .count(data_in[3:0]),
        .a(data_in[5]),
        .y(loop_y)
    );

    lint_lab_primitive_bad u_primitive_bad (
        .a(data_in[6]),
        .b(data_in[7]),
        .y(prim_y)
    );

    lint_lab_self_assign u_self_assign (
        .a(en),
        .y(self_y)
    );

    lint_lab_expr_port u_expr_port (
        .i(data_in[0] & en),
        .o(expr_y)
    );

    lint_lab_expr_port u_null_port (
        .i(data_in[1]),
        .o()
    );

    lint_lab_nested_expr_bad u_nested_expr_bad (
        .a(data_in[0]),
        .b(data_in[1]),
        .c(data_in[2]),
        .y(extra_expr_y)
    );

    lint_lab_width_bad #(
        .WIDTH(8'hff)
    ) u_width_bad (
        .a(data_in),
        .y(unconnected_y)
    );

    lint_lab_generate_bad u_generate_bad (
        .clk(clk),
        .in(data_in),
        .out()
    );
endmodule

module lint_lab_bad_seq (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output reg  q
);
    reg unused_seq_reg;
    always @(posedge clk) begin
        q = d;
        q = q;
    end
    always @(negedge rst_n) begin
        unused_seq_reg <= 1'b0;
    end
endmodule

module lint_lab_bad_comb (
    input  wire a,
    input  wire b,
    input  wire sel,
    output reg  y
);
    reg latch_reg;
    always @(a or sel) begin
        if (sel) begin
            y = a & b;
        end
    end
    always @* begin
        if (a) begin
            latch_reg = b;
        end
    end
endmodule

module lint_lab_bad_case (
    input  wire [2:0] sel,
    input  wire [7:0] a,
    output reg  [7:0] y
);
    always @* begin
        casez (sel)
            3'b000: y = a;
            3'b000: y = 8'h55;
            3'b1?0: y = 8'hxx;
            3'b0z1: y = 8'h0f;
        endcase
    end
endmodule

module lint_lab_bad_reset (
    input  wire clk,
    input  wire rst_n,
    input  wire en,
    input  wire d,
    output reg  q
);
    always @(posedge clk or posedge rst_n) begin
        if (rst_n & en) begin
            q <= 1'b0;
        end else begin
            q <= d;
        end
    end
endmodule

module lint_lab_both_edges (
    input  wire clk,
    input  wire d,
    output reg  q
);
    always @(posedge clk or negedge clk) begin
        q <= d;
    end
endmodule

module lint_lab_mixed_senselist (
    input  wire clk,
    input  wire a,
    output reg  y
);
    always @(posedge clk or a) begin
        y <= a;
    end
endmodule

module lint_lab_loop_bad (
    input  wire [3:0] count,
    input  wire       a,
    output reg        y
);
    integer i;
    always @* begin
        y = 1'b0;
        repeat (count) begin
            y = y ^ a;
        end
        for (i = 0; i < count; i = i + 1) begin
            y = y | a;
        end
    end
endmodule

module lint_lab_primitive_bad (
    input  wire a,
    input  wire b,
    output wire y
);
    and u_and_primitive (y, a, b);
endmodule

module lint_lab_self_assign (
    input  wire a,
    output reg  y
);
    always @* begin
        y = a;
        y = y;
    end
endmodule

module lint_lab_expr_port (
    input  wire i,
    output wire o
);
    assign o = i;
endmodule

module lint_lab_width_bad #(
    parameter [1:0] WIDTH = 2'b01
) (
    input  wire [7:0] a,
    output wire       y
);
    wire [2:0] narrow;
    wire signed [3:0] signed_small;
    assign narrow = a;
    assign signed_small = a[7:0];
    assign y = (narrow == 3'b??0) ? signed_small[0] : a[0];
endmodule

module lint_lab_generate_bad (
    input  wire       clk,
    input  wire [7:0] in,
    output wire [7:0] out
);
    genvar gi;
    generate
        for (gi = 0; gi < 8; gi = gi + 1) begin
            lint_lab_bad_seq u_gen_seq (
                .clk(clk),
                .rst_n(in[0]),
                .d(in[gi]),
                .q(out[gi])
            );
        end
    endgenerate
endmodule

module lint_lab_initial_delay_bad (
    input  wire a,
    output reg  y
);
    initial begin
        y = 1'b1;
    end
    always @* begin
        #1 y = a;
    end
endmodule


module lint_lab_nested_expr_bad (
    input  wire a,
    input  wire b,
    input  wire c,
    output wire y
);
    assign y = a ? (b ? c : a) : (c ? b : a);
endmodule
