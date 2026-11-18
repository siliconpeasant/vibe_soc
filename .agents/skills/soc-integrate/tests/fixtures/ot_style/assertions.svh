`define TEXTIFY(x) `"x`"
`define CHECK(name, expr) assert property (@(posedge clk_i) expr);
`define PORT_WIDTH(x) ((x) * 2)
