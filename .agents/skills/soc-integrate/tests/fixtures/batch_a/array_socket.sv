module array_socket #(
    parameter int N = 4,
    parameter bit ExplicitErrs = 1'b1,
    localparam int NWD = $clog2(ExplicitErrs ? N+1 : N)
) (
    input array_pkg::req_t host_i,
    output array_pkg::rsp_t host_o,
    output array_pkg::req_t dev_o [N],
    input array_pkg::rsp_t dev_i [N],
    input logic [NWD-1:0] select_i
);
    for (genvar i = 0; i < N; i++) begin : gen_devices
        assign dev_o[i] = host_i;
    end
    always_comb begin
        host_o = array_pkg::rsp_t'(select_i);
        for (int i = 0; i < N; i++) begin
            host_o ^= dev_i[i];
        end
    end
endmodule
