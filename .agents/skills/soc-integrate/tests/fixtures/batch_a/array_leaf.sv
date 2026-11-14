module array_leaf(input array_pkg::req_t req_i, output array_pkg::rsp_t rsp_o);
    assign rsp_o = array_pkg::rsp_t'({req_i.valid, req_i.data[7:4]} ^ req_i.data[4:0]);
endmodule
