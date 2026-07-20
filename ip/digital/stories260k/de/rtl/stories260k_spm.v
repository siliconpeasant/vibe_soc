//============================================================================
// Module     : stories260k_spm
// Function   : Behavioral scratchpad buffers (WBUF/KVBUF/ACTBUF/VECBUF)
//
// Phase-1 storage is behavioral wide-word arrays with combinational reads;
// this document-level contract matches the npu phase-1 approach. A future
// synchronous 1R1W SRAM macro replacement must register read data and keep
// the same port widths; see docs/interface_spec.md.
//
//   WBUF   : 256-bit words, mixed-W4/W8 tiles + group scales + RoPE (host-loaded)
//   KVBUF  : 256-bit words, INT4 KV cache + per-pos scales (core-managed)
//   ACTBUF : 64-bit words, INT8 working vectors; legacy score space reserved
//   VECBUF : 64-bit words, gains / requant table
//
// kv_vdata_o presents the same 8-pos x 8-head_dim INT4 tile as kv_rdata_o but
// nibble-transposed ([hd][t] rows), which the AV matmul consumes directly.
//
// Under `SYNTHESIS` this module collapses to an empty blackbox: the PD flow
// binds it to the stub macro (LEF/Liberty under pd/openroad/nangate45/).
//============================================================================

`ifdef SYNTHESIS

(* blackbox *)
(* keep_hierarchy *)
module stories260k_spm (
    input  wire         clk,
    input  wire [3:0]   host_sel_i,
    input  wire         host_we_i,
    input  wire [15:0]  host_addr_i,
    input  wire [31:0]  host_wdata_i,
    input  wire [3:0]   host_wstrb_i,
    output wire [31:0]  host_wbuf_rdata_o,
    output wire [31:0]  host_kv_rdata_o,
    output wire [31:0]  host_act_rdata_o,
    output wire [31:0]  host_vec_rdata_o,
    input  wire [12:0]  wbuf_raddr_i,
    output wire [255:0] wbuf_rdata_o,
    input  wire [12:0]  wbuf_saddr_i,
    output wire [255:0] wbuf_sdata_o,
    input  wire [12:0]  wbuf_i8_raddr_i,
    output wire [255:0] wbuf_i8_rdata_o,
    input  wire [11:0]  kv_raddr_i,
    output wire [255:0] kv_rdata_o,
    output wire [255:0] kv_vdata_o,
    input  wire [11:0]  kv_scale_raddr_i,
    output wire [255:0] kv_scale_rdata_o,
    input  wire         kv_we_i,
    input  wire [11:0]  kv_waddr_i,
    input  wire [255:0] kv_wdata_i,
    input  wire [31:0]  kv_wstrb_i,
    input  wire [8:0]   act_raddr_i,
    output wire [63:0]  act_rdata_o,
    input  wire         act_we_i,
    input  wire [8:0]   act_waddr_i,
    input  wire [63:0]  act_wdata_i,
    input  wire [7:0]   act_wstrb_i,
    input  wire [9:0]   vec_raddr_i,
    output wire [63:0]  vec_rdata_o,
    input  wire         vec_we_i,
    input  wire [9:0]   vec_waddr_i,
    input  wire [63:0]  vec_wdata_i,
    input  wire [7:0]   vec_wstrb_i
);
endmodule

`else

module stories260k_spm #(
    parameter integer WBUF_WORDS = 4736,   // 148 KiB / 32 B
    parameter integer KV_WORDS   = 3968,   // 124 KiB / 32 B
    parameter integer ACT_WORDS  = 512,    // 4 KiB / 8 B
    parameter integer VEC_WORDS  = 1024    // 8 KiB / 8 B
) (
    input  wire         clk,

    // Host port (32-bit word address; buffer contents intentionally
    // persist across resets, so there is no rst_n here)
    input  wire [3:0]   host_sel_i,    // one-hot: 0=WBUF 1=KVBUF 2=ACTBUF 3=VECBUF
    input  wire         host_we_i,
    input  wire [15:0]  host_addr_i,   // 32-bit word address inside the window
    input  wire [31:0]  host_wdata_i,
    input  wire [3:0]   host_wstrb_i,
    output wire [31:0]  host_wbuf_rdata_o,
    output wire [31:0]  host_kv_rdata_o,
    output wire [31:0]  host_act_rdata_o,
    output wire [31:0]  host_vec_rdata_o,

    // Core WBUF ports (combinational reads)
    input  wire [12:0]  wbuf_raddr_i,
    output wire [255:0] wbuf_rdata_o,
    input  wire [12:0]  wbuf_saddr_i,
    output wire [255:0] wbuf_sdata_o,
    input  wire [12:0]  wbuf_i8_raddr_i,
    output wire [255:0] wbuf_i8_rdata_o,

    // Core KVBUF ports
    input  wire [11:0]  kv_raddr_i,
    output wire [255:0] kv_rdata_o,
    output wire [255:0] kv_vdata_o,
    input  wire [11:0]  kv_scale_raddr_i,
    output wire [255:0] kv_scale_rdata_o,
    input  wire         kv_we_i,
    input  wire [11:0]  kv_waddr_i,
    input  wire [255:0] kv_wdata_i,
    input  wire [31:0]  kv_wstrb_i,

    // Core ACTBUF ports
    input  wire [8:0]   act_raddr_i,
    output wire [63:0]  act_rdata_o,
    input  wire         act_we_i,
    input  wire [8:0]   act_waddr_i,
    input  wire [63:0]  act_wdata_i,
    input  wire [7:0]   act_wstrb_i,

    // Core VECBUF ports
    input  wire [9:0]   vec_raddr_i,
    output wire [63:0]  vec_rdata_o,
    input  wire         vec_we_i,
    input  wire [9:0]   vec_waddr_i,
    input  wire [63:0]  vec_wdata_i,
    input  wire [7:0]   vec_wstrb_i
);

    reg [255:0] wbuf_mem [0:WBUF_WORDS-1];
    reg [255:0] kv_mem   [0:KV_WORDS-1];
    reg [63:0]  act_mem  [0:ACT_WORDS-1];
    reg [63:0]  vec_mem  [0:VEC_WORDS-1];

    integer i;

    // Behavioral zero-init keeps X propagation out of PoC simulations.
    // Guarded out for synthesis (yosys predefines SYNTHESIS): a real macro
    // replacement must be initialized by the host (see interface spec).
`ifndef SYNTHESIS
    initial begin
        for (i = 0; i < WBUF_WORDS; i = i + 1) wbuf_mem[i] = 256'd0;
        for (i = 0; i < KV_WORDS;   i = i + 1) kv_mem[i]   = 256'd0;
        for (i = 0; i < ACT_WORDS;  i = i + 1) act_mem[i]  = 64'd0;
        for (i = 0; i < VEC_WORDS;  i = i + 1) vec_mem[i]  = 64'd0;
    end
`endif

    // ------------------------------------------------------------------
    // Write ports: host has priority; the top level guarantees the host is
    // stalled while the core is busy, so the two never contend.
    // ------------------------------------------------------------------
    genvar b;

    generate
        for (b = 0; b < 32; b = b + 1) begin : g_wbuf_wbyte
            localparam LANE = b / 4;
            localparam BYTE = b % 4;
            always @(posedge clk) begin
                if (host_sel_i[0] && host_we_i && host_wstrb_i[BYTE] &&
                    (host_addr_i[2:0] == LANE[2:0]))
                    wbuf_mem[host_addr_i[15:3]][b*8 +: 8] <=
                        host_wdata_i[BYTE*8 +: 8];
            end
        end
    endgenerate

    generate
        for (b = 0; b < 32; b = b + 1) begin : g_kv_wbyte
            localparam LANE = b / 4;
            localparam BYTE = b % 4;
            always @(posedge clk) begin
                if (host_sel_i[1] && host_we_i && host_wstrb_i[BYTE] &&
                    (host_addr_i[2:0] == LANE[2:0]))
                    kv_mem[host_addr_i[14:3]][b*8 +: 8] <=
                        host_wdata_i[BYTE*8 +: 8];
                else if (kv_we_i && kv_wstrb_i[b])
                    kv_mem[kv_waddr_i][b*8 +: 8] <= kv_wdata_i[b*8 +: 8];
            end
        end
    endgenerate

    generate
        for (b = 0; b < 8; b = b + 1) begin : g_act_wbyte
            localparam HALF = b / 4;
            localparam BYTE = b % 4;
            always @(posedge clk) begin
                if (host_sel_i[2] && host_we_i && host_wstrb_i[BYTE] &&
                    (host_addr_i[0] == HALF[0]))
                    act_mem[host_addr_i[9:1]][b*8 +: 8] <=
                        host_wdata_i[BYTE*8 +: 8];
                else if (act_we_i && act_wstrb_i[b])
                    act_mem[act_waddr_i][b*8 +: 8] <= act_wdata_i[b*8 +: 8];
            end
        end
    endgenerate

    generate
        for (b = 0; b < 8; b = b + 1) begin : g_vec_wbyte
            localparam HALF = b / 4;
            localparam BYTE = b % 4;
            always @(posedge clk) begin
                if (host_sel_i[3] && host_we_i && host_wstrb_i[BYTE] &&
                    (host_addr_i[0] == HALF[0]))
                    vec_mem[host_addr_i[10:1]][b*8 +: 8] <=
                        host_wdata_i[BYTE*8 +: 8];
                else if (vec_we_i && vec_wstrb_i[b])
                    vec_mem[vec_waddr_i][b*8 +: 8] <= vec_wdata_i[b*8 +: 8];
            end
        end
    endgenerate

    // ------------------------------------------------------------------
    // Host readback (combinational)
    // ------------------------------------------------------------------
    assign host_wbuf_rdata_o = wbuf_mem[host_addr_i[15:3]][host_addr_i[2:0]*32 +: 32];
    assign host_kv_rdata_o   = kv_mem[host_addr_i[14:3]][host_addr_i[2:0]*32 +: 32];
    assign host_act_rdata_o  = host_addr_i[0] ?
                               act_mem[host_addr_i[9:1]][63:32] :
                               act_mem[host_addr_i[9:1]][31:0];
    assign host_vec_rdata_o  = host_addr_i[0] ?
                               vec_mem[host_addr_i[10:1]][63:32] :
                               vec_mem[host_addr_i[10:1]][31:0];

    // ------------------------------------------------------------------
    // Core read ports (combinational)
    // ------------------------------------------------------------------
    assign wbuf_rdata_o = wbuf_mem[wbuf_raddr_i];
    assign wbuf_sdata_o = wbuf_mem[wbuf_saddr_i];
    assign wbuf_i8_rdata_o = wbuf_mem[wbuf_i8_raddr_i];
    assign kv_rdata_o   = kv_mem[kv_raddr_i];
    assign kv_scale_rdata_o = kv_mem[kv_scale_raddr_i];
    assign act_rdata_o  = act_mem[act_raddr_i];
    assign vec_rdata_o  = vec_mem[vec_raddr_i];

    // V-tile nibble transpose: input word holds 8 consecutive pos x 8 hd
    // nibbles ([t][hd]); output rows are hd, lanes are t ([hd][t]).
    genvar hd, t;
    generate
        for (hd = 0; hd < 8; hd = hd + 1) begin : g_vt_row
            for (t = 0; t < 8; t = t + 1) begin : g_vt_lane
                assign kv_vdata_o[hd*32+t*4 +: 4] = kv_mem[kv_raddr_i][t*32+hd*4 +: 4];
            end
        end
    endgenerate

endmodule

`endif
