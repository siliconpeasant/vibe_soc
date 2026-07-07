//============================================================================
// Module     : tb_npu
// Function   : Self-checking standalone testbench for npu
//============================================================================

`timescale 1ns/1ps

module tb_npu;

    localparam [15:0] ADDR_CTRL           = 16'h0000;
    localparam [15:0] ADDR_STATUS         = 16'h0004;
    localparam [15:0] ADDR_CFG            = 16'h0008;
    localparam [15:0] ADDR_ACT_BASE       = 16'h000c;
    localparam [15:0] ADDR_WGT_BASE       = 16'h0010;
    localparam [15:0] ADDR_OUT_BASE       = 16'h0014;
    localparam [15:0] ADDR_ACC_INIT       = 16'h0018;
    localparam [15:0] ADDR_ACC_RESULT     = 16'h001c;
    localparam [15:0] ADDR_ERR_CODE       = 16'h0020;
    localparam [15:0] ADDR_OUT_CFG        = 16'h0024;
    localparam [15:0] ADDR_BIAS_BASE      = 16'h0028;
    localparam [15:0] ADDR_QUANT_MULT     = 16'h002c;
    localparam [15:0] ADDR_QUANT_CFG      = 16'h0030;
    localparam [15:0] ADDR_LAST_OUT_COUNT = 16'h0034;
    localparam [15:0] ADDR_ACT_SPM        = 16'h0100;
    localparam [15:0] ADDR_WGT_SPM        = 16'h0200;
    localparam [15:0] ADDR_OUT_SPM        = 16'h0300;
    localparam [15:0] ADDR_BIAS_SPM       = 16'h0400;

    localparam [4:0] ERR_START_BUSY       = 5'd1;
    localparam [4:0] ERR_DESC_ACT_RANGE   = 5'd2;
    localparam [4:0] ERR_DESC_WGT_RANGE   = 5'd3;
    localparam [4:0] ERR_DESC_OUT_RANGE   = 5'd4;
    localparam [4:0] ERR_INVALID_ADDR     = 5'd5;
    localparam [4:0] ERR_REG_UNALIGNED    = 5'd6;
    localparam [4:0] ERR_BAD_REG_WSTRB    = 5'd7;
    localparam [4:0] ERR_SPM_UNALIGNED    = 5'd8;
    localparam [4:0] ERR_DESC_BIAS_RANGE  = 5'd9;
    localparam [4:0] ERR_DESC_Q_SHIFT     = 5'd10;
    localparam [4:0] ERR_DESC_ACTIVATION  = 5'd11;
    localparam [4:0] ERR_RO_WRITE         = 5'd12;
    localparam [4:0] ERR_BIAS_BAD_WSTRB   = 5'd13;

    localparam [1:0] ACT_NONE             = 2'd0;
    localparam [1:0] ACT_RELU             = 2'd1;
    localparam [1:0] ACT_RELU6            = 2'd2;

    logic        clk;
    logic        rst_n;
    logic        mm_valid;
    logic        mm_write;
    logic [15:0] mm_addr;
    logic [31:0] mm_wdata;
    logic [3:0]  mm_wstrb;
    logic [31:0] mm_rdata;
    logic        mm_ready;
    logic        mm_error;
    logic        irq;

    int unsigned error_cnt;
    int unsigned check_cnt;
    int unsigned test_cnt;
    int unsigned rand_state;

    logic [7:0]  act_model [0:63];
    logic [7:0]  wgt_model [0:63];
    logic [7:0]  out_model [0:63];
    logic [31:0] bias_model [0:15];

    npu u_dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .mm_valid (mm_valid),
        .mm_write (mm_write),
        .mm_addr  (mm_addr),
        .mm_wdata (mm_wdata),
        .mm_wstrb (mm_wstrb),
        .mm_rdata (mm_rdata),
        .mm_ready (mm_ready),
        .mm_error (mm_error),
        .irq      (irq)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    task automatic note_test(input string name);
        begin
            test_cnt++;
            $display("[TEST] %0d %s", test_cnt, name);
        end
    endtask

    task automatic fail(input string msg);
        begin
            error_cnt++;
            $display("[FAIL] %s", msg);
        end
    endtask

    task automatic check_eq32(input string name, input [31:0] got, input [31:0] exp);
        begin
            check_cnt++;
            if (got !== exp) begin
                error_cnt++;
                $display("[FAIL] %s got=0x%08x exp=0x%08x", name, got, exp);
            end
        end
    endtask

    task automatic check_eq8(input string name, input [7:0] got, input [7:0] exp);
        begin
            check_cnt++;
            if (got !== exp) begin
                error_cnt++;
                $display("[FAIL] %s got=0x%02x exp=0x%02x", name, got, exp);
            end
        end
    endtask

    task automatic check_eq1(input string name, input got, input exp);
        begin
            check_cnt++;
            if (got !== exp) begin
                error_cnt++;
                $display("[FAIL] %s got=%0b exp=%0b", name, got, exp);
            end
        end
    endtask

    task automatic check_no_x(input string name);
        begin
            check_cnt++;
            if ($isunknown({mm_rdata, mm_ready, mm_error, irq})) begin
                error_cnt++;
                $display("[FAIL] %s visible output contains X/Z", name);
            end
        end
    endtask

    task automatic reset_models;
        int i;
        begin
            for (i = 0; i < 64; i++) begin
                act_model[i] = 8'h00;
                wgt_model[i] = 8'h00;
                out_model[i] = 8'h00;
            end
            for (i = 0; i < 16; i++) begin
                bias_model[i] = 32'h0000_0000;
            end
        end
    endtask

    task automatic drive_idle;
        begin
            mm_valid = 1'b0;
            mm_write = 1'b0;
            mm_addr  = 16'h0000;
            mm_wdata = 32'h0000_0000;
            mm_wstrb = 4'h0;
        end
    endtask

    task automatic apply_reset;
        begin
            drive_idle();
            reset_models();
            rst_n = 1'b0;
            repeat (4) @(posedge clk);
            #1;
            check_eq1("reset mm_ready", mm_ready, 1'b1);
            check_eq1("reset mm_error", mm_error, 1'b0);
            check_eq1("reset irq", irq, 1'b0);
            rst_n = 1'b1;
            repeat (2) @(posedge clk);
            #1;
            check_no_x("post reset outputs");
        end
    endtask

    task automatic mm_access(
        input  bit          write,
        input  [15:0]      addr,
        input  [31:0]      wdata,
        input  [3:0]       wstrb,
        input  bit          exp_error,
        output [31:0]      rdata,
        output int unsigned stall_cycles,
        input  string       name
    );
        bit accepted;
        bit ready_at_edge;
        begin
            stall_cycles = 0;
            accepted = 1'b0;
            @(negedge clk);
            mm_valid = 1'b1;
            mm_write = write;
            mm_addr  = addr;
            mm_wdata = wdata;
            mm_wstrb = wstrb;

            while (!accepted) begin
                @(posedge clk);
                ready_at_edge = mm_ready;
                #1;
                check_no_x({name, " outputs"});
                if (ready_at_edge) begin
                    accepted = 1'b1;
                    rdata = mm_rdata;
                    check_eq1({name, " mm_error"}, mm_error, exp_error);
                end else begin
                    stall_cycles++;
                    check_eq1({name, " stable valid"}, mm_valid, 1'b1);
                    check_eq1({name, " stable write"}, mm_write, write);
                    check_eq32({name, " stable addr"}, {16'h0000, mm_addr}, {16'h0000, addr});
                    check_eq32({name, " stable wdata"}, mm_wdata, wdata);
                    check_eq32({name, " stable wstrb"}, {28'h0, mm_wstrb}, {28'h0, wstrb});
                end
            end

            @(negedge clk);
            drive_idle();
        end
    endtask

    task automatic mm_write_ok(input [15:0] addr, input [31:0] data, input [3:0] strb);
        logic [31:0] rdata;
        int unsigned stalls;
        begin
            mm_access(1'b1, addr, data, strb, 1'b0, rdata, stalls, "write_ok");
        end
    endtask

    task automatic mm_write_err(input [15:0] addr, input [31:0] data, input [3:0] strb);
        logic [31:0] rdata;
        int unsigned stalls;
        begin
            mm_access(1'b1, addr, data, strb, 1'b1, rdata, stalls, "write_err");
        end
    endtask

    task automatic mm_read(input [15:0] addr, input bit exp_error, output [31:0] data);
        int unsigned stalls;
        begin
            mm_access(1'b0, addr, 32'h0000_0000, 4'h0, exp_error, data, stalls, "read");
        end
    endtask

    task automatic expect_read(input string name, input [15:0] addr, input [31:0] exp);
        logic [31:0] data;
        begin
            mm_read(addr, 1'b0, data);
            check_eq32(name, data, exp);
        end
    endtask

    task automatic write_act(input int unsigned offset, input [31:0] data, input [3:0] strb);
        begin
            mm_write_ok(ADDR_ACT_SPM + offset[15:0], data, strb);
            if (strb[0]) act_model[offset + 0] = data[7:0];
            if (strb[1]) act_model[offset + 1] = data[15:8];
            if (strb[2]) act_model[offset + 2] = data[23:16];
            if (strb[3]) act_model[offset + 3] = data[31:24];
        end
    endtask

    task automatic write_wgt(input int unsigned offset, input [31:0] data, input [3:0] strb);
        begin
            mm_write_ok(ADDR_WGT_SPM + offset[15:0], data, strb);
            if (strb[0]) wgt_model[offset + 0] = data[7:0];
            if (strb[1]) wgt_model[offset + 1] = data[15:8];
            if (strb[2]) wgt_model[offset + 2] = data[23:16];
            if (strb[3]) wgt_model[offset + 3] = data[31:24];
        end
    endtask

    task automatic write_out(input int unsigned offset, input [31:0] data, input [3:0] strb);
        begin
            mm_write_ok(ADDR_OUT_SPM + offset[15:0], data, strb);
            if (strb[0]) out_model[offset + 0] = data[7:0];
            if (strb[1]) out_model[offset + 1] = data[15:8];
            if (strb[2]) out_model[offset + 2] = data[23:16];
            if (strb[3]) out_model[offset + 3] = data[31:24];
        end
    endtask

    task automatic write_bias(input int unsigned index, input [31:0] data);
        begin
            mm_write_ok(ADDR_BIAS_SPM + {index[13:0], 2'b00}, data, 4'hf);
            bias_model[index] = data;
        end
    endtask

    function automatic int signed sx8(input [7:0] value);
        begin
            sx8 = {{24{value[7]}}, value};
        end
    endfunction

    function automatic longint signed sx32_to_64(input [31:0] value);
        begin
            sx32_to_64 = {{32{value[31]}}, value};
        end
    endfunction

    function automatic [31:0] make_cfg(input int unsigned k_m1, input int unsigned act_stride_m1);
        begin
            make_cfg = 32'h8000_0000 | {16'h0000, act_stride_m1[7:0], k_m1[7:0]};
        end
    endfunction

    function automatic [31:0] make_out_cfg(
        input int unsigned out_count_m1,
        input int unsigned out_stride_m1,
        input int unsigned wgt_stride_m1
    );
        begin
            make_out_cfg = {8'h00, wgt_stride_m1[7:0], out_stride_m1[7:0], out_count_m1[7:0]};
        end
    endfunction

    function automatic [31:0] make_quant_cfg(
        input int unsigned shift,
        input [7:0] zp,
        input [1:0] activation,
        input [7:0] relu6_max
    );
        begin
            make_quant_cfg = {relu6_max, 6'h00, activation, zp, 2'b00, shift[5:0]};
        end
    endfunction

    function automatic int unsigned next_rand(input int unsigned limit);
        begin
            rand_state = (rand_state * 32'd1664525) + 32'd1013904223;
            next_rand = (limit == 0) ? 0 : (rand_state % limit);
        end
    endfunction

    function automatic [31:0] pack4_s8(
        input int signed b0,
        input int signed b1,
        input int signed b2,
        input int signed b3
    );
        begin
            pack4_s8 = {b3[7:0], b2[7:0], b1[7:0], b0[7:0]};
        end
    endfunction

    task automatic quantize_scalar(
        input [31:0] post_bias,
        input [31:0] quant_mult,
        input int unsigned quant_shift,
        input [7:0] out_zero_point,
        input [1:0] activation_mode,
        input [7:0] relu6_max,
        output [7:0] out_byte,
        output bit sat_clip
    );
        longint signed product;
        longint signed shifted;
        longint signed activated;
        longint signed zp_ext;
        longint signed relu6_ext;
        begin
            product = sx32_to_64(post_bias) * sx32_to_64(quant_mult);
            if (quant_shift == 0) begin
                shifted = product;
            end else begin
                shifted = (product + (64'sd1 <<< (quant_shift - 1))) >>> quant_shift;
            end

            zp_ext = {{56{out_zero_point[7]}}, out_zero_point};
            relu6_ext = {{56{relu6_max[7]}}, relu6_max};
            activated = shifted + zp_ext;
            if (activation_mode == ACT_RELU) begin
                if (activated < zp_ext) activated = zp_ext;
            end else if (activation_mode == ACT_RELU6) begin
                if (activated < zp_ext) activated = zp_ext;
                if (activated > relu6_ext) activated = relu6_ext;
            end

            if (activated > 64'sd127) begin
                out_byte = 8'h7f;
                sat_clip = 1'b1;
            end else if (activated < -64'sd128) begin
                out_byte = 8'h80;
                sat_clip = 1'b1;
            end else begin
                out_byte = activated[7:0];
                sat_clip = 1'b0;
            end
        end
    endtask

    task automatic ref_one_output(
        input int unsigned out_idx,
        input int unsigned k_m1,
        input int unsigned act_stride_m1,
        input int unsigned act_base,
        input int unsigned wgt_base,
        input int unsigned out_stride_m1,
        input int unsigned wgt_stride_m1,
        input int unsigned bias_base,
        input [31:0] acc_init,
        input [31:0] quant_mult,
        input int unsigned quant_shift,
        input [7:0] out_zero_point,
        input [1:0] activation_mode,
        input [7:0] relu6_max,
        output [31:0] post_bias,
        output [7:0] out_byte,
        output bit sat_clip
    );
        int unsigned k;
        int unsigned lane;
        int unsigned act_addr;
        int unsigned wgt_addr;
        int signed acc;
        longint signed product;
        longint signed shifted;
        longint signed activated;
        longint signed zp_ext;
        longint signed relu6_ext;
        begin
            acc = acc_init;
            for (k = 0; k <= k_m1; k++) begin
                act_addr = act_base + (k * (act_stride_m1 + 1));
                wgt_addr = wgt_base + (out_idx * (wgt_stride_m1 + 1)) + (k * 4);
                for (lane = 0; lane < 4; lane++) begin
                    acc += sx8(act_model[act_addr + lane]) * sx8(wgt_model[wgt_addr + lane]);
                end
            end

            post_bias = acc + $signed(bias_model[bias_base + out_idx]);
            product = sx32_to_64(post_bias) * sx32_to_64(quant_mult);
            if (quant_shift == 0) begin
                shifted = product;
            end else begin
                shifted = (product + (64'sd1 <<< (quant_shift - 1))) >>> quant_shift;
            end

            zp_ext = {{56{out_zero_point[7]}}, out_zero_point};
            relu6_ext = {{56{relu6_max[7]}}, relu6_max};
            activated = shifted + zp_ext;
            if (activation_mode == ACT_RELU) begin
                if (activated < zp_ext) activated = zp_ext;
            end else if (activation_mode == ACT_RELU6) begin
                if (activated < zp_ext) activated = zp_ext;
                if (activated > relu6_ext) activated = relu6_ext;
            end

            if (activated > 64'sd127) begin
                out_byte = 8'h7f;
                sat_clip = 1'b1;
            end else if (activated < -64'sd128) begin
                out_byte = 8'h80;
                sat_clip = 1'b1;
            end else begin
                out_byte = activated[7:0];
                sat_clip = 1'b0;
            end
        end
    endtask

    task automatic clear_done_error_sat;
        begin
            mm_write_ok(ADDR_STATUS, 32'h0000_000e, 4'hf);
        end
    endtask

    task automatic soft_reset;
        begin
            mm_write_ok(ADDR_CTRL, 32'h0000_0002, 4'hf);
            repeat (2) @(posedge clk);
            reset_models();
        end
    endtask

    task automatic wait_done_or_error;
        logic [31:0] status;
        int unsigned timeout;
        begin
            timeout = 0;
            status = 32'h0;
            while (((status & 32'h0000_0006) == 32'h0) && (timeout < 200)) begin
                mm_read(ADDR_STATUS, 1'b0, status);
                timeout++;
            end
            if (timeout >= 200) begin
                fail("timeout waiting for done or error");
            end
        end
    endtask

    task automatic program_command(
        input int unsigned k_m1,
        input int unsigned act_stride_m1,
        input int unsigned act_base,
        input int unsigned wgt_base,
        input int unsigned out_base,
        input [31:0] acc_init,
        input int unsigned out_count_m1,
        input int unsigned out_stride_m1,
        input int unsigned wgt_stride_m1,
        input int unsigned bias_base,
        input [31:0] quant_mult,
        input int unsigned quant_shift,
        input [7:0] out_zero_point,
        input [1:0] activation_mode,
        input [7:0] relu6_max
    );
        begin
            mm_write_ok(ADDR_CFG, make_cfg(k_m1, act_stride_m1), 4'hf);
            mm_write_ok(ADDR_ACT_BASE, {24'h0, act_base[7:0]}, 4'hf);
            mm_write_ok(ADDR_WGT_BASE, {24'h0, wgt_base[7:0]}, 4'hf);
            mm_write_ok(ADDR_OUT_BASE, {24'h0, out_base[7:0]}, 4'hf);
            mm_write_ok(ADDR_ACC_INIT, acc_init, 4'hf);
            mm_write_ok(ADDR_OUT_CFG, make_out_cfg(out_count_m1, out_stride_m1, wgt_stride_m1), 4'hf);
            mm_write_ok(ADDR_BIAS_BASE, {28'h0, bias_base[3:0]}, 4'hf);
            mm_write_ok(ADDR_QUANT_MULT, quant_mult, 4'hf);
            mm_write_ok(ADDR_QUANT_CFG, make_quant_cfg(quant_shift, out_zero_point, activation_mode, relu6_max), 4'hf);
        end
    endtask

    task automatic expect_err_code(input string name, input [4:0] exp_code);
        logic [31:0] code;
        begin
            mm_read(ADDR_ERR_CODE, 1'b0, code);
            check_eq32(name, code, {27'h0, exp_code});
        end
    endtask

    task automatic start_and_check_success(
        input string name,
        input int unsigned k_m1,
        input int unsigned act_stride_m1,
        input int unsigned act_base,
        input int unsigned wgt_base,
        input int unsigned out_base,
        input [31:0] acc_init,
        input int unsigned out_count_m1,
        input int unsigned out_stride_m1,
        input int unsigned wgt_stride_m1,
        input int unsigned bias_base,
        input [31:0] quant_mult,
        input int unsigned quant_shift,
        input [7:0] out_zero_point,
        input [1:0] activation_mode,
        input [7:0] relu6_max,
        input bit exp_sat
    );
        logic [31:0] status;
        logic [31:0] acc_result;
        logic [31:0] last_count;
        logic [31:0] out_word;
        logic [31:0] exp_post_bias;
        logic [7:0] exp_byte;
        logic [7:0] exp_count;
        bit sat_clip;
        bit any_sat;
        int unsigned out_idx;
        int unsigned out_addr;
        int unsigned out_word_addr;
        int unsigned lane_shift;
        begin
            clear_done_error_sat();
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1({name, " status done"}, status[1], 1'b1);
            check_eq1({name, " status error"}, status[2], 1'b0);
            check_eq1({name, " status busy"}, status[0], 1'b0);

            any_sat = 1'b0;
            for (out_idx = 0; out_idx <= out_count_m1; out_idx++) begin
                ref_one_output(out_idx, k_m1, act_stride_m1, act_base, wgt_base,
                               out_stride_m1, wgt_stride_m1, bias_base, acc_init,
                               quant_mult, quant_shift, out_zero_point,
                               activation_mode, relu6_max, exp_post_bias,
                               exp_byte, sat_clip);
                any_sat |= sat_clip;
                out_addr = out_base + (out_idx * (out_stride_m1 + 1));
                out_word_addr = out_addr & 32'hffff_fffc;
                lane_shift = (out_addr & 32'h3) * 8;
                mm_read(ADDR_OUT_SPM + out_word_addr[15:0], 1'b0, out_word);
                check_eq8({name, " output byte"}, out_word[lane_shift +: 8], exp_byte);
                out_model[out_addr] = exp_byte;
            end

            ref_one_output(out_count_m1, k_m1, act_stride_m1, act_base, wgt_base,
                           out_stride_m1, wgt_stride_m1, bias_base, acc_init,
                           quant_mult, quant_shift, out_zero_point,
                           activation_mode, relu6_max, exp_post_bias,
                           exp_byte, sat_clip);
            mm_read(ADDR_ACC_RESULT, 1'b0, acc_result);
            check_eq32({name, " acc_result"}, acc_result, exp_post_bias);
            exp_count = out_count_m1 + 1;
            mm_read(ADDR_LAST_OUT_COUNT, 1'b0, last_count);
            check_eq32({name, " last_out_count"}, last_count, {24'h0, exp_count});
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1({name, " saturation sticky"}, status[3], exp_sat);
            check_eq1({name, " reference saturation"}, any_sat, exp_sat);
        end
    endtask

    task automatic start_and_expect_descriptor_error(input string name, input [4:0] exp_code);
        logic [31:0] status;
        begin
            clear_done_error_sat();
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1({name, " done clear"}, status[1], 1'b0);
            check_eq1({name, " error set"}, status[2], 1'b1);
            expect_err_code({name, " err_code"}, exp_code);
            expect_read({name, " last_out_count zero"}, ADDR_LAST_OUT_COUNT, 32'h0000_0000);
        end
    endtask

    task automatic test_reset_defaults;
        logic [31:0] data;
        int i;
        begin
            note_test("reset defaults");
            apply_reset();
            expect_read("CTRL reset", ADDR_CTRL, 32'h0000_0000);
            expect_read("STATUS reset", ADDR_STATUS, 32'h0000_0000);
            expect_read("CFG reset", ADDR_CFG, 32'h8000_0300);
            expect_read("ACT_BASE reset", ADDR_ACT_BASE, 32'h0000_0000);
            expect_read("WGT_BASE reset", ADDR_WGT_BASE, 32'h0000_0000);
            expect_read("OUT_BASE reset", ADDR_OUT_BASE, 32'h0000_0000);
            expect_read("ACC_INIT reset", ADDR_ACC_INIT, 32'h0000_0000);
            expect_read("ACC_RESULT reset", ADDR_ACC_RESULT, 32'h0000_0000);
            expect_read("ERR_CODE reset", ADDR_ERR_CODE, 32'h0000_0000);
            expect_read("OUT_CFG reset", ADDR_OUT_CFG, 32'h0003_0000);
            expect_read("BIAS_BASE reset", ADDR_BIAS_BASE, 32'h0000_0000);
            expect_read("QUANT_MULT reset", ADDR_QUANT_MULT, 32'h0000_0001);
            expect_read("QUANT_CFG reset", ADDR_QUANT_CFG, 32'h7f00_0000);
            expect_read("LAST_OUT_COUNT reset", ADDR_LAST_OUT_COUNT, 32'h0000_0000);
            for (i = 0; i < 64; i += 4) begin
                mm_read(ADDR_ACT_SPM + i[15:0], 1'b0, data);
                check_eq32("ACT_SPM reset", data, 32'h0000_0000);
                mm_read(ADDR_WGT_SPM + i[15:0], 1'b0, data);
                check_eq32("WGT_SPM reset", data, 32'h0000_0000);
                mm_read(ADDR_OUT_SPM + i[15:0], 1'b0, data);
                check_eq32("OUT_SPM reset", data, 32'h0000_0000);
                mm_read(ADDR_BIAS_SPM + i[15:0], 1'b0, data);
                check_eq32("BIAS_SPM reset", data, 32'h0000_0000);
            end
            check_eq1("irq reset low", irq, 1'b0);
        end
    endtask

    task automatic test_register_rw;
        logic [31:0] data;
        begin
            note_test("register write read");
            soft_reset();
            mm_write_ok(ADDR_CFG, 32'hffff_0a02, 4'hf);
            expect_read("CFG writable and RO bits", ADDR_CFG, 32'h8000_0a02);
            mm_write_ok(ADDR_ACT_BASE, 32'haaaa_0011, 4'hf);
            mm_write_ok(ADDR_WGT_BASE, 32'h5555_0022, 4'hf);
            mm_write_ok(ADDR_OUT_BASE, 32'hffff_0033, 4'hf);
            mm_write_ok(ADDR_ACC_INIT, 32'h1234_5678, 4'hf);
            mm_write_ok(ADDR_OUT_CFG, 32'hff09_0807, 4'hf);
            mm_write_ok(ADDR_BIAS_BASE, 32'hffff_fff5, 4'hf);
            mm_write_ok(ADDR_QUANT_MULT, 32'hffff_fffd, 4'hf);
            mm_write_ok(ADDR_QUANT_CFG, 32'h8235_aa1f, 4'hf);
            expect_read("ACT_BASE field", ADDR_ACT_BASE, 32'h0000_0011);
            expect_read("WGT_BASE field", ADDR_WGT_BASE, 32'h0000_0022);
            expect_read("OUT_BASE field", ADDR_OUT_BASE, 32'h0000_0033);
            expect_read("ACC_INIT field", ADDR_ACC_INIT, 32'h1234_5678);
            expect_read("OUT_CFG fields", ADDR_OUT_CFG, 32'h0009_0807);
            expect_read("BIAS_BASE field", ADDR_BIAS_BASE, 32'h0000_0005);
            expect_read("QUANT_MULT field", ADDR_QUANT_MULT, 32'hffff_fffd);
            expect_read("QUANT_CFG fields", ADDR_QUANT_CFG, 32'h8201_aa1f);
            mm_write_ok(ADDR_CTRL, 32'h0000_0004, 4'hf);
            expect_read("CTRL irq_en only", ADDR_CTRL, 32'h0000_0004);
            check_eq1("irq no source", irq, 1'b0);

            mm_read(16'h0040, 1'b1, data);
            mm_read(ADDR_STATUS, 1'b0, data);
            check_eq1("sticky error before W1C", data[2], 1'b1);
            mm_write_ok(ADDR_STATUS, 32'h0000_0004, 4'hf);
            expect_read("STATUS error W1C", ADDR_STATUS, 32'h0000_0000);
        end
    endtask

    task automatic test_scratchpad_byte_lanes;
        begin
            note_test("scratchpad byte lanes");
            soft_reset();
            write_act(4, 32'h1122_3344, 4'hf);
            write_act(4, 32'haabb_ccdd, 4'h5);
            expect_read("ACT byte lanes 0 and 2", ADDR_ACT_SPM + 16'h0004, 32'h11bb_33dd);
            write_wgt(16, 32'h5566_7788, 4'ha);
            expect_read("WGT byte lanes 1 and 3", ADDR_WGT_SPM + 16'h0010, 32'h5500_7700);
            write_out(60, 32'h0102_0304, 4'h0);
            expect_read("OUT zero strobe no-op", ADDR_OUT_SPM + 16'h003c, 32'h0000_0000);
            write_out(60, 32'h0102_0304, 4'hf);
            expect_read("OUT last word", ADDR_OUT_SPM + 16'h003c, 32'h0102_0304);
        end
    endtask

    task automatic test_bias_scratchpad;
        logic [31:0] data;
        int i;
        begin
            note_test("bias scratchpad access");
            soft_reset();
            for (i = 0; i < 16; i++) begin
                write_bias(i, 32'h8000_0000 + i[31:0]);
                mm_read(ADDR_BIAS_SPM + {i[13:0], 2'b00}, 1'b0, data);
                check_eq32("BIAS readback", data, 32'h8000_0000 + i[31:0]);
            end
            mm_write_err(ADDR_BIAS_SPM + 16'h0014, 32'h1111_2222, 4'h3);
            expect_err_code("bias bad strobe err_code", ERR_BIAS_BAD_WSTRB);
            mm_read(ADDR_BIAS_SPM + 16'h0014, 1'b0, data);
            check_eq32("bad bias strobe preserved", data, bias_model[5]);
        end
    endtask

    task automatic test_backward_dot_product;
        begin
            note_test("backward-compatible dot product");
            soft_reset();
            write_act(0, 32'h04fd_0201, 4'hf);
            write_wgt(0, 32'h0203_fe05, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(0, 3, 0, 0, 0, 32'h0000_0007, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_check_success("dot product", 0, 3, 0, 0, 0, 32'h0000_0007,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'h00,
                                    ACT_NONE, 8'h7f, 1'b0);
        end
    endtask

    task automatic test_multi_output_quant_bias_activation;
        begin
            note_test("multi-output bias quant activation");
            soft_reset();
            write_act(0, 32'h02ff_0304, 4'hf);
            write_act(4, 32'h80fe_0000, 4'hc);
            write_act(8, 32'h0000_017f, 4'h3);
            write_wgt(0,  32'h01ff_0201, 4'hf);
            write_wgt(4,  32'h02fe_0100, 4'hf);
            write_wgt(12, 32'hff02_0001, 4'hf);
            write_wgt(16, 32'h0301_ff02, 4'hf);
            write_wgt(24, 32'h0101_0101, 4'hf);
            write_wgt(28, 32'hff00_0201, 4'hf);
            write_bias(1, 32'h0000_0005);
            write_bias(2, 32'hffff_fff0);
            write_bias(3, 32'h0000_0020);
            write_out(8, 32'haa55_33cc, 4'hf);
            program_command(1, 5, 0, 0, 8, 32'hffff_fff8, 2, 1, 11, 1,
                            32'h0000_0003, 1, 8'hfb, ACT_RELU6, 8'h20);
            start_and_check_success("multi output", 1, 5, 0, 0, 8, 32'hffff_fff8,
                                    2, 1, 11, 1, 32'h0000_0003, 1, 8'hfb,
                                    ACT_RELU6, 8'h20, 1'b0);
            expect_read("output stride preserved", ADDR_OUT_SPM + 16'h0008,
                        {out_model[11], out_model[10], out_model[9], out_model[8]});
        end
    endtask

    task automatic test_toy_mlp_end_to_end;
        int signed input_vec [0:15];
        int signed l1_wgt [0:7][0:15];
        int signed l1_bias [0:7];
        int signed l2_wgt [0:3][0:7];
        int signed l2_bias [0:3];
        logic [7:0] hidden_exp [0:7];
        logic [7:0] logits_exp [0:3];
        logic [7:0] logits_got [0:3];
        logic [31:0] status;
        logic [31:0] data;
        logic [31:0] hidden_word0;
        logic [31:0] hidden_word1;
        logic [31:0] post_bias;
        bit sat_clip;
        int signed acc;
        int signed exp_best;
        int signed got_best;
        int unsigned exp_class;
        int unsigned got_class;
        int out_i;
        int in_i;
        int group_i;
        begin
            note_test("toy MLP end-to-end inference");
            soft_reset();

            for (out_i = 0; out_i < 8; out_i++) begin
                l1_bias[out_i] = 0;
                for (in_i = 0; in_i < 16; in_i++) begin
                    l1_wgt[out_i][in_i] = 0;
                end
            end
            for (out_i = 0; out_i < 4; out_i++) begin
                l2_bias[out_i] = 0;
                for (in_i = 0; in_i < 8; in_i++) begin
                    l2_wgt[out_i][in_i] = 0;
                end
            end

            input_vec[0]  =  3; input_vec[1]  = -2; input_vec[2]  =  1; input_vec[3]  =  4;
            input_vec[4]  = -1; input_vec[5]  =  2; input_vec[6]  = -3; input_vec[7]  =  1;
            input_vec[8]  =  0; input_vec[9]  =  5; input_vec[10] = -4; input_vec[11] =  2;
            input_vec[12] =  1; input_vec[13] = -1; input_vec[14] =  3; input_vec[15] = -2;

            l1_bias[0] =  1; l1_bias[1] = -2; l1_bias[2] =  0; l1_bias[3] =  3;
            l1_bias[4] = -1; l1_bias[5] =  2; l1_bias[6] =  0; l1_bias[7] =  1;

            l1_wgt[0][0] = 1;  l1_wgt[0][2] = -1; l1_wgt[0][3] = 2;  l1_wgt[0][5] = 1;
            l1_wgt[0][6] = 1;  l1_wgt[0][7] = -1; l1_wgt[0][8] = 1;  l1_wgt[0][11] = 1;
            l1_wgt[0][12] = -1; l1_wgt[0][13] = 1;
            l1_wgt[1][0] = -1; l1_wgt[1][1] = 1;  l1_wgt[1][4] = 1;  l1_wgt[1][5] = -1;
            l1_wgt[1][7] = 1;  l1_wgt[1][9] = -1; l1_wgt[1][10] = 1; l1_wgt[1][12] = 1;
            l1_wgt[1][14] = -1; l1_wgt[1][15] = 1;
            l1_wgt[2][1] = 1;  l1_wgt[2][2] = 1;  l1_wgt[2][4] = -1; l1_wgt[2][6] = 2;
            l1_wgt[2][8] = 1;  l1_wgt[2][9] = 1;  l1_wgt[2][11] = -1; l1_wgt[2][13] = 1;
            l1_wgt[2][14] = -1;
            l1_wgt[3][0] = 1;  l1_wgt[3][1] = 1;  l1_wgt[3][2] = 1;  l1_wgt[3][3] = 1;
            l1_wgt[3][4] = 1;  l1_wgt[3][5] = 1;  l1_wgt[3][6] = 1;  l1_wgt[3][7] = 1;
            l1_wgt[3][12] = -1; l1_wgt[3][13] = -1; l1_wgt[3][14] = -1; l1_wgt[3][15] = -1;
            l1_wgt[4][0] = 2;  l1_wgt[4][1] = -1; l1_wgt[4][3] = 1;  l1_wgt[4][6] = -1;
            l1_wgt[4][7] = 1;  l1_wgt[4][8] = 1;  l1_wgt[4][9] = -1; l1_wgt[4][13] = 1;
            l1_wgt[4][15] = -1;
            l1_wgt[5][2] = 1;  l1_wgt[5][3] = -1; l1_wgt[5][4] = 1;  l1_wgt[5][5] = 1;
            l1_wgt[5][8] = -1; l1_wgt[5][10] = 1; l1_wgt[5][11] = 1; l1_wgt[5][12] = -1;
            l1_wgt[5][14] = 1;
            l1_wgt[6][0] = 1;  l1_wgt[6][1] = -2; l1_wgt[6][2] = 1;  l1_wgt[6][4] = 2;
            l1_wgt[6][5] = -1; l1_wgt[6][6] = 1;  l1_wgt[6][9] = 1;  l1_wgt[6][10] = -1;
            l1_wgt[6][11] = 1; l1_wgt[6][12] = 1; l1_wgt[6][15] = 1;
            l1_wgt[7][0] = -1; l1_wgt[7][3] = -1; l1_wgt[7][5] = 1;  l1_wgt[7][6] = -1;
            l1_wgt[7][7] = 1;  l1_wgt[7][8] = -1; l1_wgt[7][11] = 1; l1_wgt[7][13] = -1;
            l1_wgt[7][14] = 1; l1_wgt[7][15] = -1;

            l2_bias[0] = 0; l2_bias[1] = 2; l2_bias[2] = -1; l2_bias[3] = 0;
            l2_wgt[0][0] = 1;  l2_wgt[0][2] = -1; l2_wgt[0][3] = 1;  l2_wgt[0][5] = 1;  l2_wgt[0][6] = -1;
            l2_wgt[1][1] = 1;  l2_wgt[1][2] = 1;  l2_wgt[1][3] = -1; l2_wgt[1][4] = 1;  l2_wgt[1][7] = 1;
            l2_wgt[2][0] = -1; l2_wgt[2][3] = 1;  l2_wgt[2][4] = -1; l2_wgt[2][5] = 1;  l2_wgt[2][6] = 1;
            l2_wgt[3][0] = 1;  l2_wgt[3][1] = -1; l2_wgt[3][5] = -1; l2_wgt[3][6] = 1;  l2_wgt[3][7] = 1;

            for (out_i = 0; out_i < 8; out_i++) begin
                acc = l1_bias[out_i];
                for (in_i = 0; in_i < 16; in_i++) begin
                    acc += input_vec[in_i] * l1_wgt[out_i][in_i];
                end
                post_bias = acc;
                quantize_scalar(post_bias, 32'h0000_0001, 0, 8'h00, ACT_RELU, 8'h7f,
                                hidden_exp[out_i], sat_clip);
            end

            for (out_i = 0; out_i < 4; out_i++) begin
                acc = l2_bias[out_i];
                for (in_i = 0; in_i < 8; in_i++) begin
                    acc += sx8(hidden_exp[in_i]) * l2_wgt[out_i][in_i];
                end
                post_bias = acc;
                quantize_scalar(post_bias, 32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f,
                                logits_exp[out_i], sat_clip);
            end

            for (group_i = 0; group_i < 16; group_i += 4) begin
                write_act(group_i, pack4_s8(input_vec[group_i + 0], input_vec[group_i + 1],
                                            input_vec[group_i + 2], input_vec[group_i + 3]), 4'hf);
            end

            for (out_i = 0; out_i < 4; out_i++) begin
                for (group_i = 0; group_i < 16; group_i += 4) begin
                    write_wgt((out_i * 16) + group_i,
                              pack4_s8(l1_wgt[out_i][group_i + 0], l1_wgt[out_i][group_i + 1],
                                       l1_wgt[out_i][group_i + 2], l1_wgt[out_i][group_i + 3]), 4'hf);
                end
                write_bias(out_i, l1_bias[out_i]);
            end
            program_command(3, 3, 0, 0, 0, 32'h0000_0000, 3, 0, 15, 0,
                            32'h0000_0001, 0, 8'h00, ACT_RELU, 8'h7f);
            clear_done_error_sat();
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1("toy_mlp layer1a done", status[1], 1'b1);
            check_eq1("toy_mlp layer1a error", status[2], 1'b0);
            expect_read("toy_mlp layer1a last_out_count", ADDR_LAST_OUT_COUNT, 32'h0000_0004);

            for (out_i = 4; out_i < 8; out_i++) begin
                for (group_i = 0; group_i < 16; group_i += 4) begin
                    write_wgt(((out_i - 4) * 16) + group_i,
                              pack4_s8(l1_wgt[out_i][group_i + 0], l1_wgt[out_i][group_i + 1],
                                       l1_wgt[out_i][group_i + 2], l1_wgt[out_i][group_i + 3]), 4'hf);
                end
                write_bias(out_i - 4, l1_bias[out_i]);
            end
            program_command(3, 3, 0, 0, 4, 32'h0000_0000, 3, 0, 15, 0,
                            32'h0000_0001, 0, 8'h00, ACT_RELU, 8'h7f);
            clear_done_error_sat();
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1("toy_mlp layer1b done", status[1], 1'b1);
            check_eq1("toy_mlp layer1b error", status[2], 1'b0);
            expect_read("toy_mlp layer1b last_out_count", ADDR_LAST_OUT_COUNT, 32'h0000_0004);

            mm_read(ADDR_OUT_SPM + 16'h0000, 1'b0, hidden_word0);
            mm_read(ADDR_OUT_SPM + 16'h0004, 1'b0, hidden_word1);
            for (out_i = 0; out_i < 4; out_i++) begin
                check_eq8("toy_mlp hidden byte", hidden_word0[out_i * 8 +: 8], hidden_exp[out_i]);
            end
            for (out_i = 0; out_i < 4; out_i++) begin
                check_eq8("toy_mlp hidden byte", hidden_word1[out_i * 8 +: 8], hidden_exp[out_i + 4]);
            end

            write_act(0, hidden_word0, 4'hf);
            write_act(4, hidden_word1, 4'hf);

            for (out_i = 0; out_i < 4; out_i++) begin
                for (group_i = 0; group_i < 8; group_i += 4) begin
                    write_wgt((out_i * 8) + group_i,
                              pack4_s8(l2_wgt[out_i][group_i + 0], l2_wgt[out_i][group_i + 1],
                                       l2_wgt[out_i][group_i + 2], l2_wgt[out_i][group_i + 3]), 4'hf);
                end
                write_bias(out_i, l2_bias[out_i]);
            end
            program_command(1, 3, 0, 0, 0, 32'h0000_0000, 3, 0, 7, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            clear_done_error_sat();
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1("toy_mlp layer2 done", status[1], 1'b1);
            check_eq1("toy_mlp layer2 error", status[2], 1'b0);
            expect_read("toy_mlp layer2 last_out_count", ADDR_LAST_OUT_COUNT, 32'h0000_0004);

            mm_read(ADDR_OUT_SPM + 16'h0000, 1'b0, data);
            for (out_i = 0; out_i < 4; out_i++) begin
                logits_got[out_i] = data[out_i * 8 +: 8];
                check_eq8("toy_mlp final logit", logits_got[out_i], logits_exp[out_i]);
            end

            exp_class = 0;
            got_class = 0;
            exp_best = sx8(logits_exp[0]);
            got_best = sx8(logits_got[0]);
            for (out_i = 1; out_i < 4; out_i++) begin
                if (sx8(logits_exp[out_i]) > exp_best) begin
                    exp_best = sx8(logits_exp[out_i]);
                    exp_class = out_i;
                end
                if (sx8(logits_got[out_i]) > got_best) begin
                    got_best = sx8(logits_got[out_i]);
                    got_class = out_i;
                end
            end
            check_eq32("toy_mlp argmax", {30'h0, got_class[1:0]}, {30'h0, exp_class[1:0]});
            $display("[MODEL] toy_mlp expected_class=%0d got_class=%0d", exp_class, got_class);
        end
    endtask

    task automatic test_activation_modes_and_zero_point;
        begin
            note_test("activation modes and zero point");
            soft_reset();
            write_act(0, 32'h0101_0101, 4'hf);
            write_wgt(0, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(0, 3, 0, 0, 0, 32'hffff_fff0, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h0a, ACT_NONE, 8'h7f);
            start_and_check_success("activation none", 0, 3, 0, 0, 0, 32'hffff_fff0,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'h0a,
                                    ACT_NONE, 8'h7f, 1'b0);

            program_command(0, 3, 0, 0, 1, 32'hffff_fff0, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h0a, ACT_RELU, 8'h7f);
            start_and_check_success("activation relu", 0, 3, 0, 0, 1, 32'hffff_fff0,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'h0a,
                                    ACT_RELU, 8'h7f, 1'b0);

            program_command(0, 3, 0, 0, 2, 32'h0000_0020, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'hf8, ACT_RELU6, 8'h06);
            start_and_check_success("activation relu6", 0, 3, 0, 0, 2, 32'h0000_0020,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'hf8,
                                    ACT_RELU6, 8'h06, 1'b0);
        end
    endtask

    task automatic test_saturation_high_low;
        begin
            note_test("saturation high low");
            soft_reset();
            write_act(0, 32'h0101_0101, 4'hf);
            write_wgt(0, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(0, 3, 0, 0, 0, 32'h0000_00c8, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_check_success("sat high", 0, 3, 0, 0, 0, 32'h0000_00c8,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'h00,
                                    ACT_NONE, 8'h7f, 1'b1);

            program_command(0, 3, 0, 0, 1, 32'hffff_ff38, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_check_success("sat low", 0, 3, 0, 0, 1, 32'hffff_ff38,
                                    0, 0, 3, 0, 32'h0000_0001, 0, 8'h00,
                                    ACT_NONE, 8'h7f, 1'b1);
        end
    endtask

    task automatic test_negative_multiplier_shift;
        begin
            note_test("negative multiplier and rounding shift");
            soft_reset();
            write_act(0, 32'h0302_0101, 4'hf);
            write_wgt(0, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0003);
            program_command(0, 3, 0, 0, 4, 32'h0000_0000, 0, 0, 3, 0,
                            32'hffff_fffd, 2, 8'h00, ACT_NONE, 8'h7f);
            start_and_check_success("negative multiplier", 0, 3, 0, 0, 4, 32'h0000_0000,
                                    0, 0, 3, 0, 32'hffff_fffd, 2, 8'h00,
                                    ACT_NONE, 8'h7f, 1'b0);
        end
    endtask

    task automatic test_start_while_busy;
        logic [31:0] status;
        begin
            note_test("start while busy");
            soft_reset();
            write_out(0, 32'h5555_5555, 4'hf);
            write_act(0,  32'h0101_0101, 4'hf);
            write_act(4,  32'h0101_0101, 4'hf);
            write_act(8,  32'h0101_0101, 4'hf);
            write_act(12, 32'h0101_0101, 4'hf);
            write_wgt(0,  32'h0101_0101, 4'hf);
            write_wgt(4,  32'h0101_0101, 4'hf);
            write_wgt(8,  32'h0101_0101, 4'hf);
            write_wgt(12, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(3, 3, 0, 0, 0, 32'h0000_0000, 1, 0, 15, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            @(posedge clk);
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            repeat (2) @(posedge clk);
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1("start busy done clear", status[1], 1'b0);
            check_eq1("start busy error set", status[2], 1'b1);
            expect_err_code("start busy code", ERR_START_BUSY);
            expect_read("aborted output unchanged", ADDR_OUT_SPM, 32'h5555_5555);
        end
    endtask

    task automatic test_descriptor_errors;
        begin
            note_test("descriptor errors");
            soft_reset();
            program_command(0, 3, 61, 0, 0, 32'h0, 0, 0, 3, 0, 32'h1, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_expect_descriptor_error("act range", ERR_DESC_ACT_RANGE);

            soft_reset();
            program_command(0, 3, 0, 61, 0, 32'h0, 0, 0, 3, 0, 32'h1, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_expect_descriptor_error("wgt range", ERR_DESC_WGT_RANGE);

            soft_reset();
            program_command(0, 3, 0, 0, 64, 32'h0, 0, 0, 3, 0, 32'h1, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_expect_descriptor_error("out range", ERR_DESC_OUT_RANGE);

            soft_reset();
            program_command(0, 3, 0, 0, 0, 32'h0, 3, 0, 3, 13, 32'h1, 0, 8'h00, ACT_NONE, 8'h7f);
            start_and_expect_descriptor_error("bias range", ERR_DESC_BIAS_RANGE);

            soft_reset();
            program_command(0, 3, 0, 0, 0, 32'h0, 0, 0, 3, 0, 32'h1, 32, 8'h00, ACT_NONE, 8'h7f);
            start_and_expect_descriptor_error("quant shift", ERR_DESC_Q_SHIFT);

            soft_reset();
            program_command(0, 3, 0, 0, 0, 32'h0, 0, 0, 3, 0, 32'h1, 0, 8'h00, 2'd3, 8'h7f);
            start_and_expect_descriptor_error("activation mode", ERR_DESC_ACTIVATION);

            soft_reset();
            program_command(0, 3, 0, 0, 0, 32'h0, 0, 0, 3, 0, 32'h1, 0, 8'h10, ACT_RELU6, 8'h0f);
            start_and_expect_descriptor_error("relu6 config", ERR_DESC_ACTIVATION);
        end
    endtask

    task automatic test_illegal_accesses;
        logic [31:0] data;
        begin
            note_test("illegal access and RO writes");
            soft_reset();
            mm_write_ok(ADDR_CFG, make_cfg(5, 3), 4'hf);
            mm_read(16'h0040, 1'b1, data);
            expect_err_code("invalid address code", ERR_INVALID_ADDR);
            mm_read(16'h0001, 1'b1, data);
            expect_err_code("unaligned register code", ERR_REG_UNALIGNED);
            mm_write_err(ADDR_CFG, make_cfg(9, 3), 4'h1);
            expect_err_code("bad reg wstrb code", ERR_BAD_REG_WSTRB);
            expect_read("bad wstrb did not modify CFG", ADDR_CFG, make_cfg(5, 3));
            mm_write_err(ADDR_ACC_RESULT, 32'hffff_ffff, 4'hf);
            expect_err_code("ACC_RESULT read-only code", ERR_RO_WRITE);
            mm_write_err(ADDR_LAST_OUT_COUNT, 32'hffff_ffff, 4'hf);
            expect_err_code("LAST_OUT_COUNT read-only code", ERR_RO_WRITE);
            mm_read(ADDR_ACT_SPM + 16'h0001, 1'b1, data);
            expect_err_code("unaligned scratchpad code", ERR_SPM_UNALIGNED);
        end
    endtask

    task automatic test_scratchpad_busy_stall;
        logic [31:0] data;
        int unsigned stalls;
        begin
            note_test("scratchpad busy stall");
            soft_reset();
            write_act(0, 32'h0101_0101, 4'hf);
            write_act(4, 32'h0202_0202, 4'hf);
            write_wgt(0, 32'h0101_0101, 4'hf);
            write_wgt(4, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(1, 3, 0, 0, 0, 32'h0000_0000, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            mm_write_ok(ADDR_CTRL, 32'h0000_0001, 4'hf);
            mm_access(1'b0, ADDR_ACT_SPM, 32'h0, 4'h0, 1'b0, data, stalls, "busy_spm_read");
            check_cnt++;
            if (stalls == 0) begin
                error_cnt++;
                $display("[FAIL] scratchpad read did not stall while busy");
            end
            check_eq32("busy stalled read data", data, 32'h0101_0101);
        end
    endtask

    task automatic test_irq_done_error;
        logic [31:0] status;
        begin
            note_test("irq done and error behavior");
            soft_reset();
            mm_write_ok(ADDR_CTRL, 32'h0000_0004, 4'hf);
            write_act(0, 32'h0101_0101, 4'hf);
            write_wgt(0, 32'h0101_0101, 4'hf);
            write_bias(0, 32'h0000_0000);
            program_command(0, 3, 0, 0, 0, 32'h0000_0000, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            mm_write_ok(ADDR_CTRL, 32'h0000_0005, 4'hf);
            wait_done_or_error();
            check_eq1("irq done asserted", irq, 1'b1);
            mm_write_ok(ADDR_STATUS, 32'h0000_0002, 4'hf);
            @(posedge clk);
            #1;
            check_eq1("irq done clear", irq, 1'b0);

            mm_write_ok(ADDR_CTRL, 32'h0000_0004, 4'hf);
            program_command(0, 3, 61, 0, 0, 32'h0000_0000, 0, 0, 3, 0,
                            32'h0000_0001, 0, 8'h00, ACT_NONE, 8'h7f);
            mm_write_ok(ADDR_CTRL, 32'h0000_0005, 4'hf);
            wait_done_or_error();
            mm_read(ADDR_STATUS, 1'b0, status);
            check_eq1("irq error status", status[2], 1'b1);
            check_eq1("irq error asserted", irq, 1'b1);
            mm_write_ok(ADDR_CTRL, 32'h0000_0014, 4'hf);
            @(posedge clk);
            #1;
            check_eq1("irq error clear", irq, 1'b0);
        end
    endtask

    task automatic test_soft_reset;
        begin
            note_test("soft reset");
            soft_reset();
            mm_write_ok(ADDR_CFG, make_cfg(3, 7), 4'hf);
            mm_write_ok(ADDR_ACT_BASE, 32'h0000_0010, 4'hf);
            mm_write_ok(ADDR_WGT_BASE, 32'h0000_0020, 4'hf);
            mm_write_ok(ADDR_OUT_BASE, 32'h0000_0001, 4'hf);
            mm_write_ok(ADDR_ACC_INIT, 32'hdead_beef, 4'hf);
            mm_write_ok(ADDR_OUT_CFG, make_out_cfg(2, 3, 7), 4'hf);
            mm_write_ok(ADDR_BIAS_BASE, 32'h0000_0004, 4'hf);
            mm_write_ok(ADDR_QUANT_MULT, 32'h0000_0009, 4'hf);
            mm_write_ok(ADDR_QUANT_CFG, make_quant_cfg(3, 8'hf0, ACT_RELU, 8'h7f), 4'hf);
            write_act(0, 32'hffff_ffff, 4'hf);
            write_wgt(0, 32'haaaa_5555, 4'hf);
            write_out(0, 32'h1234_5678, 4'hf);
            write_bias(0, 32'h8765_4321);
            mm_write_ok(ADDR_CTRL, 32'h0000_0006, 4'hf);
            repeat (2) @(posedge clk);
            reset_models();
            expect_read("soft reset CFG", ADDR_CFG, 32'h8000_0300);
            expect_read("soft reset OUT_CFG", ADDR_OUT_CFG, 32'h0003_0000);
            expect_read("soft reset QUANT_MULT", ADDR_QUANT_MULT, 32'h0000_0001);
            expect_read("soft reset QUANT_CFG", ADDR_QUANT_CFG, 32'h7f00_0000);
            expect_read("soft reset ACT_SPM", ADDR_ACT_SPM, 32'h0000_0000);
            expect_read("soft reset WGT_SPM", ADDR_WGT_SPM, 32'h0000_0000);
            expect_read("soft reset OUT_SPM", ADDR_OUT_SPM, 32'h0000_0000);
            expect_read("soft reset BIAS_SPM", ADDR_BIAS_SPM, 32'h0000_0000);
            expect_read("soft reset STATUS", ADDR_STATUS, 32'h0000_0000);
            check_eq1("soft reset irq", irq, 1'b0);
        end
    endtask

    task automatic test_seeded_random_cases;
        int t;
        int i;
        int signed val0;
        int signed val1;
        int signed val2;
        int signed val3;
        int signed acc_seed;
        logic [31:0] act_word;
        logic [31:0] wgt_word;
        logic [31:0] bias_word;
        begin
            note_test("seeded random inference cases");
            rand_state = 32'h0000_0001;
            for (t = 0; t < 6; t++) begin
                soft_reset();
                for (i = 0; i < 8; i += 4) begin
                    val0 = int'(next_rand(5)) - 2;
                    val1 = int'(next_rand(5)) - 2;
                    val2 = int'(next_rand(5)) - 2;
                    val3 = int'(next_rand(5)) - 2;
                    act_word = {val3[7:0], val2[7:0], val1[7:0], val0[7:0]};
                    val0 = int'(next_rand(5)) - 2;
                    val1 = int'(next_rand(5)) - 2;
                    val2 = int'(next_rand(5)) - 2;
                    val3 = int'(next_rand(5)) - 2;
                    wgt_word = {val3[7:0], val2[7:0], val1[7:0], val0[7:0]};
                    write_act(i, act_word, 4'hf);
                    write_wgt(i, wgt_word, 4'hf);
                end
                bias_word = int'(next_rand(17)) - 8;
                write_bias(0, bias_word);
                acc_seed = int'(next_rand(9)) - 4;
                program_command(1, 3, 0, 0, t[7:0], acc_seed, 0, 0, 3, 0,
                                32'h0000_0001, 1, 8'h00, ACT_NONE, 8'h7f);
                start_and_check_success("seeded random", 1, 3, 0, 0, t[7:0], acc_seed,
                                        0, 0, 3, 0, 32'h0000_0001, 1, 8'h00,
                                        ACT_NONE, 8'h7f, 1'b0);
            end
        end
    endtask

    initial begin
        error_cnt = 0;
        check_cnt = 0;
        test_cnt = 0;
        rand_state = 32'h0000_0001;
        rst_n = 1'b0;
        drive_idle();
        reset_models();

        test_reset_defaults();
        test_register_rw();
        test_scratchpad_byte_lanes();
        test_bias_scratchpad();
        test_backward_dot_product();
        test_multi_output_quant_bias_activation();
        test_toy_mlp_end_to_end();
        test_activation_modes_and_zero_point();
        test_saturation_high_low();
        test_negative_multiplier_shift();
        test_start_while_busy();
        test_descriptor_errors();
        test_illegal_accesses();
        test_scratchpad_busy_stall();
        test_irq_done_error();
        test_soft_reset();
        test_seeded_random_cases();

        repeat (5) @(posedge clk);
        $display("[SUMMARY] tests=%0d checks=%0d errors=%0d", test_cnt, check_cnt, error_cnt);
        if (error_cnt == 0) begin
            $display("RESULT: ALL TESTS PASS");
        end else begin
            $display("RESULT: TESTS FAILED");
        end
        $finish;
    end

endmodule
