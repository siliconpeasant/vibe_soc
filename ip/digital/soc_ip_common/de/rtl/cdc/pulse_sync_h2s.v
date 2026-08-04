// Module   : pulse_sync_h2s
// Function : Single-clock-cycle pulse transfer from src domain to dst domain.

module pulse_sync_h2s (
    input  wire src_clk,
    input  wire src_rst_n,
    input  wire src_pulse,
    input  wire dst_clk,
    input  wire dst_rst_n,
    output wire dst_pulse
);

    // Toggle on each accepted src pulse.
    reg src_tog;
    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n)
            src_tog <= 1'b0;
        else if (src_pulse)
            src_tog <= ~src_tog;
    end

    // 3-stage sync into destination domain, edge-detect for one-cycle pulse.
    reg [2:0] dst_sync;
    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n)
            dst_sync <= 3'b000;
        else
            dst_sync <= {dst_sync[1:0], src_tog};
    end

    assign dst_pulse = dst_sync[2] ^ dst_sync[1];

endmodule
