module body_types(a, y);
    parameter int N = 8;
    input logic [N-1:0] a;
    typedef logic [N-1:0] local_word_t;
    output local_word_t y;
    logic [N-1:0] body_value;
    localparam int BODY_BITS = $bits(body_value);
    localparam int CHECK_BITS = BODY_BITS;
    body_helper #(.W(CHECK_BITS)) u_helper (.a(a), .y(body_value));
    assign y = body_value;
endmodule
