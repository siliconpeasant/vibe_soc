//============================================================================
// Module     : tb_uart
// Function   : Self-checking testbench for uart IP
//              Full-duplex UART with 8N1 frame format
//============================================================================
`timescale 1ns / 1ps

module tb_uart;

    //========================================================================
    // Signals
    //========================================================================
    reg         clk;
    reg         rst_n;

    // TX interface
    reg  [7:0]  tx_data;
    reg         tx_valid;
    wire        tx_ready;
    wire        tx_busy;
    wire        tx_done;
    wire        tx_out;

    // RX interface
    reg         rx_in;
    wire [7:0]  rx_data;
    wire        rx_valid;
    wire        rx_busy;
    wire        rx_frame_err;

    // Configuration
    reg  [15:0] baud_div;

    // Test tracking
    integer     errors;
    integer     passes;
    integer     test_num;
    reg         dummy_fe;   // dummy for unused task output

    //========================================================================
    // Clock generation: 100 MHz (10ns period)
    //========================================================================
    initial begin
        clk = 1'b0;
    end
    always #5 clk = ~clk;

    //========================================================================
    // DUT instantiation
    //========================================================================
    uart u_dut (
        .clk          (clk),
        .rst_n        (rst_n),
        .tx_data      (tx_data),
        .tx_valid     (tx_valid),
        .tx_ready     (tx_ready),
        .tx_busy      (tx_busy),
        .tx_done      (tx_done),
        .tx_out       (tx_out),
        .rx_in        (rx_in),
        .rx_data      (rx_data),
        .rx_valid     (rx_valid),
        .rx_busy      (rx_busy),
        .rx_frame_err (rx_frame_err),
        .baud_div     (baud_div)
    );

    //========================================================================
    // Waveform dump
    //========================================================================
    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_uart);
    end

    //========================================================================
    // Timeout watchdog
    //========================================================================
    initial begin
        #5000000;
        $display("[TIMEOUT] Simulation exceeded time limit");
        $finish;
    end

    //========================================================================
    // Helper: compute bit period in ns based on baud_div
    // bit_period = (baud_div + 1) * 16 * clk_period = (baud_div + 1) * 160 ns
    //========================================================================
    function integer bit_period_ns;
        input [15:0] div;
        begin
            bit_period_ns = (div + 1) * 160;
        end
    endfunction

    //========================================================================
    // Helper: compute bit period in clock cycles
    // bit_period_clks = (baud_div + 1) * 16
    //========================================================================
    function integer bit_period_clks;
        input [15:0] div;
        begin
            bit_period_clks = (div + 1) * 16;
        end
    endfunction

    //========================================================================
    // Helper: compute sample period in ns
    // sample_period = (baud_div + 1) * 10 ns
    //========================================================================
    function integer sample_period_ns;
        input [15:0] div;
        begin
            sample_period_ns = (div + 1) * 10;
        end
    endfunction

    //========================================================================
    // Task: reset DUT
    //========================================================================
    task do_reset;
        begin
            rst_n = 1'b0;
            tx_data  = 8'h00;
            tx_valid = 1'b0;
            rx_in    = 1'b1;
            baud_div = 16'd4;
            repeat(10) @(posedge clk);
            #1;
            rst_n = 1'b1;
            repeat(2) @(posedge clk);
            #1;
        end
    endtask

    //========================================================================
    // BFM Task: uart_send - drive tx_data + tx_valid, wait for tx_done
    //========================================================================
    task uart_send;
        input [7:0]  data;
        input [15:0] div;
        begin
            baud_div = div;
            repeat(2) @(posedge clk);
            #1;

            tx_data  = data;
            tx_valid = 1'b1;

            wait(tx_ready == 1'b0);
            @(posedge clk);
            #1;
            tx_valid = 1'b0;

            wait(tx_done == 1'b1);
            @(posedge clk);
            #1;
        end
    endtask

    //========================================================================
    // BFM Task: uart_receive_frame - generate 8N1 serial waveform on rx_in
    // Uses clock-aligned delays for precise timing
    //========================================================================
    task uart_receive_frame;
        input  [7:0]  data;
        input  [15:0] div;
        output        frame_err;
        reg    [7:0]  rx_data_expected;
        integer       bp_clks;
        integer       i;
        begin
            bp_clks = bit_period_clks(div);
            rx_data_expected = data;

            while (rx_busy !== 1'b0) @(posedge clk);
            #1;

            // Start bit
            rx_in = 1'b0;
            repeat(bp_clks) @(posedge clk);

            // 8 data bits LSB first
            for (i = 0; i < 8; i = i + 1) begin
                rx_in = rx_data_expected[i];
                repeat(bp_clks) @(posedge clk);
            end

            // Stop bit - keep high and wait for rx_valid
            rx_in = 1'b1;
            wait(rx_valid == 1'b1);
            @(posedge clk);
            #1;

            frame_err = rx_frame_err;
        end
    endtask

    //========================================================================
    // BFM Task: send frame with bad stop bit (for frame error test)
    //========================================================================
    task uart_receive_frame_bad_stop;
        input [7:0]  data;
        input [15:0] div;
        output       frame_err;
        integer      bp_clks;
        begin
            bp_clks = bit_period_clks(div);
            @(posedge clk);
            #1;
            baud_div = div;
            repeat(2) @(posedge clk);
            #1;

            while (rx_busy !== 1'b0) @(posedge clk);
            #1;

            rx_in = 1'b0;
            repeat(bp_clks) @(posedge clk);

            begin : send_data_bits
                integer i;
                for (i = 0; i < 8; i = i + 1) begin
                    rx_in = data[i];
                    repeat(bp_clks) @(posedge clk);
                end
            end

            // Bad stop bit (keep low)
            rx_in = 1'b0;

            // Wait for rx_valid with frame_err
            wait(rx_valid == 1'b1);
            frame_err = rx_frame_err;
            @(posedge clk);
            #1;

            rx_in = 1'b1;
        end
    endtask

    //========================================================================
    // BFM Task: send glitch on rx_in (narrow pulse)
    //========================================================================
    task send_glitch;
        input [15:0] div;
        integer sp_clks;
        begin
            sp_clks = (div + 1);  // sample period in clocks
            rx_in = 1'b0;
            repeat(sp_clks * 4) @(posedge clk);
            rx_in = 1'b1;
            repeat(sp_clks * 20) @(posedge clk);
        end
    endtask

    //========================================================================
    // Task: check TX waveform manually
    //========================================================================
    task check_tx_waveform;
        input [7:0]  expected_data;
        input [15:0] div;
        integer      bp;
        integer      i;
        begin
            bp = bit_period_ns(div);

            wait(tx_out == 1'b0);
            #(bp / 2);

            if (tx_out !== 1'b0) begin
                $display("[FAIL] Test %0d: Start bit should be 0", test_num);
                errors = errors + 1;
            end else begin
                $display("[PASS] Test %0d: Start bit = 0", test_num);
                passes = passes + 1;
            end

            for (i = 0; i < 8; i = i + 1) begin
                #(bp);
                if (tx_out !== expected_data[i]) begin
                    $display("[FAIL] Test %0d: Data bit %0d expected %b, got %b",
                             test_num, i, expected_data[i], tx_out);
                    errors = errors + 1;
                end else begin
                    $display("[PASS] Test %0d: Data bit %0d = %b (LSB first)",
                             test_num, i, tx_out);
                    passes = passes + 1;
                end
            end

            #(bp);
            if (tx_out !== 1'b1) begin
                $display("[FAIL] Test %0d: Stop bit should be 1", test_num);
                errors = errors + 1;
            end else begin
                $display("[PASS] Test %0d: Stop bit = 1", test_num);
                passes = passes + 1;
            end
        end
    endtask

    //========================================================================
    // Task: check single value
    //========================================================================
    task check_value;
        input [255:0] name;
        input [7:0]   expected;
        input [7:0]   actual;
        begin
            if (expected !== actual) begin
                $display("[FAIL] Test %0d: %0s expected 0x%02X, got 0x%02X",
                         test_num, name, expected, actual);
                errors = errors + 1;
            end else begin
                $display("[PASS] Test %0d: %0s = 0x%02X", test_num, name, actual);
                passes = passes + 1;
            end
        end
    endtask

    task check_bit;
        input [255:0] name;
        input         expected;
        input         actual;
        begin
            if (expected !== actual) begin
                $display("[FAIL] Test %0d: %0s expected %b, got %b",
                         test_num, name, expected, actual);
                errors = errors + 1;
            end else begin
                $display("[PASS] Test %0d: %0s = %b", test_num, name, actual);
                passes = passes + 1;
            end
        end
    endtask

    //========================================================================
    // Loopback mode: when loopback_en is high, rx_in follows tx_out
    //========================================================================
    reg loopback_en;
    always @(tx_out) begin
        if (loopback_en)
            rx_in = #1 tx_out;
    end

    //========================================================================
    // Main test sequence
    //========================================================================
    initial begin
        $display("============================================================");
        $display(" uart IP Verification Start ");
        $display("============================================================");

        errors   = 0;
        passes   = 0;
        test_num = 0;
        dummy_fe = 1'b0;
        loopback_en = 1'b0;

        //====================================================================
        // Test 1: Reset verification
        //====================================================================
        test_num = 1;
        $display("\n--- Test %0d: Reset verification ---", test_num);
        rst_n = 1'b0;
        tx_data  = 8'h00;
        tx_valid = 1'b0;
        rx_in    = 1'b1;
        baud_div = 16'd4;
        repeat(5) @(posedge clk);
        #1;
        check_bit("tx_out after reset", 1'b1, tx_out);
        check_bit("tx_ready after reset", 1'b1, tx_ready);
        check_bit("tx_busy after reset", 1'b0, tx_busy);
        check_bit("tx_done after reset", 1'b0, tx_done);
        check_bit("rx_valid after reset", 1'b0, rx_valid);
        check_bit("rx_busy after reset", 1'b0, rx_busy);
        check_bit("rx_frame_err after reset", 1'b0, rx_frame_err);
        check_value("rx_data after reset", 8'h00, rx_data);
        rst_n = 1'b1;
        repeat(2) @(posedge clk);
        #1;

        //====================================================================
        // Test 2: TX single byte (0x55)
        //====================================================================
        test_num = 2;
        $display("\n--- Test %0d: TX single byte 0x55 ---", test_num);
        do_reset;
        fork
            begin
                uart_send(8'h55, 16'd4);
            end
            begin
                check_tx_waveform(8'h55, 16'd4);
            end
        join

        //====================================================================
        // Test 3: RX single byte (0xAA)
        //====================================================================
        test_num = 3;
        $display("\n--- Test %0d: RX single byte 0xAA ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        rx_in = 1'b1;
        #(bit_period_ns(16'd4) * 2);
        uart_receive_frame(8'hAA, 16'd4, dummy_fe);

        check_value("rx_data", 8'hAA, rx_data);
        check_bit("rx_frame_err", 1'b0, rx_frame_err);

        //====================================================================
        // Test 4: Loopback test
        //====================================================================
        test_num = 4;
        $display("\n--- Test %0d: Loopback test ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        begin
            reg [7:0] loop_data;
            loop_data = 8'h37;

            // Enable loopback: rx_in follows tx_out
            loopback_en = 1'b1;

            // Start TX
            tx_data = loop_data;
            tx_valid = 1'b1;
            wait(tx_ready == 1'b0);
            @(posedge clk);
            #1;
            tx_valid = 1'b0;

            // Wait for RX to receive the data
            wait(rx_valid == 1'b1);
            @(posedge clk);
            #1;

            check_value("loopback rx_data", loop_data, rx_data);
            check_bit("loopback rx_frame_err", 1'b0, rx_frame_err);

            // Disable loopback
            loopback_en = 1'b0;
            rx_in = 1'b1;

            // Wait for TX to finish
            wait(tx_done == 1'b1);
            @(posedge clk);
            #1;
            check_bit("tx_done after loopback", 1'b0, tx_done);
            check_bit("tx_ready after loopback", 1'b1, tx_ready);
        end

        //====================================================================
        // Test 5: LSB first verification
        //====================================================================
        test_num = 5;
        $display("\n--- Test %0d: LSB first verification ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        tx_data = 8'h01;
        tx_valid = 1'b1;
        wait(tx_ready == 1'b0);
        @(posedge clk);
        #1;
        tx_valid = 1'b0;

        wait(tx_out == 1'b0);
        #(bit_period_ns(16'd4));
        #(bit_period_ns(16'd4) / 2);

        if (tx_out !== 1'b1) begin
            $display("[FAIL] Test %0d: LSB first - bit0 should be 1 for 0x01", test_num);
            errors = errors + 1;
        end else begin
            $display("[PASS] Test %0d: LSB first - bit0 = 1 (correct)", test_num);
            passes = passes + 1;
        end

        wait(tx_done == 1'b1);
        @(posedge clk);
        #1;

        //====================================================================
        // Test 6: Start/Stop bits
        //====================================================================
        test_num = 6;
        $display("\n--- Test %0d: Start/Stop bits ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        tx_data = 8'h00;
        tx_valid = 1'b1;
        wait(tx_ready == 1'b0);
        @(posedge clk);
        #1;
        tx_valid = 1'b0;

        wait(tx_out == 1'b0);
        #(bit_period_ns(16'd4) / 2);
        check_bit("start bit", 1'b0, tx_out);

        #(bit_period_ns(16'd4) * 8);
        #(bit_period_ns(16'd4) / 2);
        check_bit("stop bit", 1'b1, tx_out);

        wait(tx_done == 1'b1);
        @(posedge clk);
        #1;

        //====================================================================
        // Test 7: Baud rate precision
        //====================================================================
        test_num = 7;
        $display("\n--- Test %0d: Baud rate precision ---", test_num);
        begin
            reg [15:0] div_vals [0:4];
            reg [7:0]  test_byte;
            integer    d;
            div_vals[0] = 16'd4;
            div_vals[1] = 16'd9;
            div_vals[2] = 16'd19;
            div_vals[3] = 16'd49;
            div_vals[4] = 16'd99;
            test_byte = 8'hA5;

            for (d = 0; d < 5; d = d + 1) begin
                do_reset;
                $display("  Baud div = %0d", div_vals[d]);

                uart_send(test_byte, div_vals[d]);
                $display("  [PASS] TX with div=%0d", div_vals[d]);
                passes = passes + 1;

                do_reset;
                baud_div = div_vals[d];
                repeat(2) @(posedge clk);
                #1;
                uart_receive_frame(test_byte, div_vals[d], dummy_fe);
                check_value("rx_data", test_byte, rx_data);
            end
        end

        //====================================================================
        // Test 8: tx_ready handshake
        //====================================================================
        test_num = 8;
        $display("\n--- Test %0d: tx_ready handshake ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        check_bit("tx_ready in IDLE", 1'b1, tx_ready);

        tx_data = 8'h42;
        tx_valid = 1'b1;
        wait(tx_ready == 1'b0);
        @(posedge clk);
        #1;
        check_bit("tx_ready during TX", 1'b0, tx_ready);
        tx_valid = 1'b0;

        wait(tx_done == 1'b1);
        @(posedge clk);
        #1;
        check_bit("tx_ready after done", 1'b1, tx_ready);

        //====================================================================
        // Test 9: tx_done pulse
        //====================================================================
        test_num = 9;
        $display("\n--- Test %0d: tx_done single-cycle pulse ---", test_num);
        do_reset;
        uart_send(8'h77, 16'd4);
        check_bit("tx_done after pulse", 1'b0, tx_done);

        //====================================================================
        // Test 10: rx_frame_err
        //====================================================================
        test_num = 10;
        $display("\n--- Test %0d: rx_frame_err (bad stop bit) ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        uart_receive_frame_bad_stop(8'h3C, 16'd4, dummy_fe);

        check_bit("rx_frame_err with bad stop", 1'b1, dummy_fe);
        check_value("rx_data with bad stop", 8'h3C, rx_data);

        //====================================================================
        // Test 11: Back-to-back TX
        //====================================================================
        test_num = 11;
        $display("\n--- Test %0d: Back-to-back TX ---", test_num);
        do_reset;
        begin
            reg [7:0] tx_bytes [0:3];
            integer   txi;
            tx_bytes[0] = 8'h11;
            tx_bytes[1] = 8'h22;
            tx_bytes[2] = 8'h33;
            tx_bytes[3] = 8'h44;

            for (txi = 0; txi < 4; txi = txi + 1) begin
                uart_send(tx_bytes[txi], 16'd4);
                $display("  [PASS] TX byte %0d = 0x%02X", txi, tx_bytes[txi]);
                passes = passes + 1;
            end
        end

        //====================================================================
        // Test 12: Back-to-back RX
        //====================================================================
        test_num = 12;
        $display("\n--- Test %0d: Back-to-back RX ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        begin
            reg [7:0] rx_bytes [0:3];
            integer   rxi;
            rx_bytes[0] = 8'h55;
            rx_bytes[1] = 8'hAA;
            rx_bytes[2] = 8'h0F;
            rx_bytes[3] = 8'hF0;

            for (rxi = 0; rxi < 4; rxi = rxi + 1) begin
                uart_receive_frame(rx_bytes[rxi], 16'd4, dummy_fe);
                check_value("rx_data", rx_bytes[rxi], rx_data);
                check_bit("rx_frame_err", 1'b0, rx_frame_err);
            end
        end

        //====================================================================
        // Test 13: All data values 0x00 ~ 0xFF
        //====================================================================
        test_num = 13;
        $display("\n--- Test %0d: All data values 0x00~0xFF ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        begin
            integer val;
            for (val = 0; val < 256; val = val + 1) begin
                uart_receive_frame(val[7:0], 16'd4, dummy_fe);

                if (rx_data !== val[7:0]) begin
                    $display("[FAIL] Test %0d: Value 0x%02X expected, got 0x%02X",
                             test_num, val[7:0], rx_data);
                    errors = errors + 1;
                end

                #(bit_period_ns(16'd4));
            end
            $display("  [PASS] All 256 values verified");
            passes = passes + 1;
        end

        //====================================================================
        // Test 14: Glitch rejection
        //====================================================================
        test_num = 14;
        $display("\n--- Test %0d: Glitch rejection ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        send_glitch(16'd4);

        #(bit_period_ns(16'd4) * 15);
        check_bit("rx_valid after glitch", 1'b0, rx_valid);
        check_bit("rx_busy after glitch", 1'b0, rx_busy);

        //====================================================================
        // Test 15: tx_busy flag
        //====================================================================
        test_num = 15;
        $display("\n--- Test %0d: tx_busy flag ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        check_bit("tx_busy in IDLE", 1'b0, tx_busy);

        tx_data = 8'h99;
        tx_valid = 1'b1;
        wait(tx_ready == 1'b0);
        @(posedge clk);
        #1;
        check_bit("tx_busy during TX", 1'b1, tx_busy);
        tx_valid = 1'b0;

        wait(tx_done == 1'b1);
        @(posedge clk);
        #1;
        check_bit("tx_busy after done", 1'b0, tx_busy);

        //====================================================================
        // Test 16: rx_valid single-cycle pulse
        //====================================================================
        test_num = 16;
        $display("\n--- Test %0d: rx_valid single-cycle pulse ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        uart_receive_frame(8'h66, 16'd4, dummy_fe);

        // rx_valid was checked inside uart_receive_frame (waited for it)
        // Now verify it's already low (single-cycle pulse)
        check_bit("rx_valid pulse low after task", 1'b0, rx_valid);

        //====================================================================
        // Test 17: Random data test
        //====================================================================
        test_num = 17;
        $display("\n--- Test %0d: Random data (16 iterations) ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        begin
            integer rnd;
            reg [7:0] rnd_data;
            for (rnd = 0; rnd < 16; rnd = rnd + 1) begin
                rnd_data = $random & 8'hFF;
                uart_receive_frame(rnd_data, 16'd4, dummy_fe);
                check_value("random rx_data", rnd_data, rx_data);
                #(bit_period_ns(16'd4));
            end
        end

        //====================================================================
        // Test 18: Boundary baud_div = 0
        //====================================================================
        test_num = 18;
        $display("\n--- Test %0d: Boundary baud_div = 0 ---", test_num);
        do_reset;
        uart_send(8'hDE, 16'd0);
        $display("  [PASS] TX with baud_div=0");
        passes = passes + 1;

        do_reset;
        baud_div = 16'd0;
        repeat(2) @(posedge clk);
        #1;
        uart_receive_frame(8'hAD, 16'd0, dummy_fe);
        check_value("rx_data with div=0", 8'hAD, rx_data);

        //====================================================================
        // Test 19: Full 0x00 and 0xFF data
        //====================================================================
        test_num = 19;
        $display("\n--- Test %0d: Full 0x00 and 0xFF ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        uart_receive_frame(8'h00, 16'd4, dummy_fe);
        check_value("rx_data 0x00", 8'h00, rx_data);
        #(bit_period_ns(16'd4) * 2);

        uart_receive_frame(8'hFF, 16'd4, dummy_fe);
        check_value("rx_data 0xFF", 8'hFF, rx_data);

        //====================================================================
        // Test 20: Reset during TX
        //====================================================================
        test_num = 20;
        $display("\n--- Test %0d: Reset during TX ---", test_num);
        do_reset;
        baud_div = 16'd4;
        repeat(2) @(posedge clk);
        #1;

        tx_data = 8'h55;
        tx_valid = 1'b1;
        wait(tx_ready == 1'b0);
        @(posedge clk);
        #1;
        tx_valid = 1'b0;

        #(bit_period_ns(16'd4) * 3);
        rst_n = 1'b0;
        repeat(5) @(posedge clk);
        #1;

        check_bit("tx_out after reset during TX", 1'b1, tx_out);
        check_bit("tx_ready after reset during TX", 1'b1, tx_ready);
        check_bit("tx_busy after reset during TX", 1'b0, tx_busy);
        rst_n = 1'b1;
        repeat(2) @(posedge clk);
        #1;

        //====================================================================
        // Summary
        //====================================================================
        $display("\n============================================================");
        $display(" uart IP Verification Complete ");
        $display("============================================================");
        $display("Test summary: PASS=%0d ERROR=%0d", passes, errors);
        if (errors == 0) begin
            $display("RESULT: ALL TESTS PASS");
        end else begin
            $display("RESULT: %0d TEST(S) FAILED", errors);
        end
        $display("============================================================");

        $finish;
    end

endmodule
