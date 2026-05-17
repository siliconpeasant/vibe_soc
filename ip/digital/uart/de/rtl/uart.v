//============================================================================
// Module     : uart
// Function   : Full-duplex UART with 8N1 frame format and programmable baud rate
// Author     : soc-rtl-designer
// Version    : 1.0
//============================================================================

module uart (
    // System
    input  wire        clk,
    input  wire        rst_n,

    // TX interface
    input  wire [7:0]  tx_data,
    input  wire        tx_valid,
    output reg         tx_ready,
    output reg         tx_busy,
    output reg         tx_done,
    output reg         tx_out,

    // RX interface
    input  wire        rx_in,
    output reg  [7:0]  rx_data,
    output reg         rx_valid,
    output reg         rx_busy,
    output reg         rx_frame_err,

    // Configuration
    input  wire [15:0] baud_div
);

    //========================================================================
    // Parameters
    //========================================================================
    localparam DATA_WIDTH    = 8;
    localparam BAUD_DIV_WIDTH = 16;
    localparam OVERSAMPLE    = 16;

    // TX state encoding
    localparam TX_IDLE  = 2'b00;
    localparam TX_START = 2'b01;
    localparam TX_DATA  = 2'b10;
    localparam TX_STOP  = 2'b11;

    // RX state encoding
    localparam RX_IDLE  = 3'b000;
    localparam RX_START = 3'b001;
    localparam RX_DATA  = 3'b010;
    localparam RX_STOP  = 3'b011;
    localparam RX_DONE  = 3'b100;

    //========================================================================
    // RX Input Synchronizer (2-stage)
    //========================================================================
    reg rx_in_sync0;
    reg rx_in_sync1;
    wire rx_in_sync;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_in_sync0 <= 1'b1;
            rx_in_sync1 <= 1'b1;
        end else begin
            rx_in_sync0 <= rx_in;
            rx_in_sync1 <= rx_in_sync0;
        end
    end

    assign rx_in_sync = rx_in_sync1;

    //========================================================================
    // Baud Rate Generator
    //========================================================================
    // baud_tick: one pulse per bit period (baud_div + 1) * 16 clk cycles
    // sample_tick: one pulse per sample period (baud_div + 1) clk cycles, 16x per bit
    reg [15:0] baud_cnt;
    reg        sample_tick;
    reg [3:0]  sample_cnt;
    reg        baud_tick;

    // sample_tick generation: counter wraps at baud_div
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_cnt     <= 16'd0;
            sample_tick  <= 1'b0;
        end else begin
            if (baud_cnt >= baud_div) begin
                baud_cnt    <= 16'd0;
                sample_tick <= 1'b1;
            end else begin
                baud_cnt    <= baud_cnt + 16'd1;
                sample_tick <= 1'b0;
            end
        end
    end

    // sample_cnt: 0~15, increments on sample_tick
    // baud_tick: asserted when sample_cnt == 15 and sample_tick == 1 (end of bit period)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_cnt <= 4'd0;
            baud_tick  <= 1'b0;
        end else if (sample_tick) begin
            if (sample_cnt == 4'd15) begin
                sample_cnt <= 4'd0;
                baud_tick  <= 1'b1;
            end else begin
                sample_cnt <= sample_cnt + 4'd1;
                baud_tick  <= 1'b0;
            end
        end else begin
            baud_tick <= 1'b0;
        end
    end

    //========================================================================
    // TX Controller
    //========================================================================
    reg [1:0]  tx_state;
    reg [3:0]  tx_bit_cnt;
    reg [7:0]  tx_shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_state     <= TX_IDLE;
            tx_shift_reg <= 8'h00;
            tx_bit_cnt   <= 4'd0;
            tx_out       <= 1'b1;
            tx_ready     <= 1'b1;
            tx_busy      <= 1'b0;
            tx_done      <= 1'b0;
        end else begin
            // Default: tx_done is a single-cycle pulse
            tx_done <= 1'b0;

            case (tx_state)
                TX_IDLE: begin
                    tx_out   <= 1'b1;
                    tx_ready <= 1'b1;
                    tx_busy  <= 1'b0;
                    if (tx_valid && tx_ready) begin
                        tx_shift_reg <= tx_data;
                        tx_ready     <= 1'b0;
                        tx_busy      <= 1'b1;
                        tx_state     <= TX_START;
                    end
                end

                TX_START: begin
                    tx_out <= 1'b0; // start bit
                    if (baud_tick) begin
                        tx_bit_cnt <= 4'd0;
                        tx_state   <= TX_DATA;
                    end
                end

                TX_DATA: begin
                    tx_out <= tx_shift_reg[0];
                    if (baud_tick) begin
                        tx_shift_reg <= {1'b0, tx_shift_reg[7:1]};
                        if (tx_bit_cnt == 4'd7) begin
                            tx_state <= TX_STOP;
                        end else begin
                            tx_bit_cnt <= tx_bit_cnt + 4'd1;
                        end
                    end
                end

                TX_STOP: begin
                    tx_out <= 1'b1; // stop bit
                    if (baud_tick) begin
                        tx_done  <= 1'b1;
                        tx_busy  <= 1'b0;
                        tx_ready <= 1'b1;
                        tx_state <= TX_IDLE;
                    end
                end

                default: begin
                    tx_state <= TX_IDLE;
                end
            endcase
        end
    end

    //========================================================================
    // RX Controller
    //========================================================================
    reg [2:0]  rx_state;
    reg [3:0]  rx_bit_cnt;
    reg [7:0]  rx_shift_reg;
    reg [3:0]  rx_sample_cnt;
    reg        rx_in_sync_d;
    wire       rx_falling_edge;

    // Detect falling edge on synchronized rx_in
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_in_sync_d <= 1'b1;
        end else begin
            rx_in_sync_d <= rx_in_sync;
        end
    end

    assign rx_falling_edge = rx_in_sync_d && (!rx_in_sync);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_state      <= RX_IDLE;
            rx_bit_cnt    <= 4'd0;
            rx_sample_cnt <= 4'd0;
            rx_shift_reg  <= 8'h00;
            rx_data       <= 8'h00;
            rx_valid      <= 1'b0;
            rx_busy       <= 1'b0;
            rx_frame_err  <= 1'b0;
        end else begin
            // Default: rx_valid is a single-cycle pulse
            rx_valid <= 1'b0;

            case (rx_state)
                RX_IDLE: begin
                    rx_busy       <= 1'b0;
                    rx_frame_err  <= 1'b0;
                    rx_sample_cnt <= 4'd0;
                    rx_bit_cnt    <= 4'd0;
                    // Detect start bit (falling edge and current low)
                    if (rx_falling_edge && (rx_in_sync == 1'b0)) begin
                        rx_busy  <= 1'b1;
                        rx_state <= RX_START;
                    end
                end

                RX_START: begin
                    if (sample_tick) begin
                        if (rx_sample_cnt == 4'd7) begin
                            // At half bit time, confirm still low
                            if (rx_in_sync == 1'b0) begin
                                rx_sample_cnt <= 4'd0;
                                rx_bit_cnt    <= 4'd0;
                                rx_state      <= RX_DATA;
                            end else begin
                                // Glitch, return to idle
                                rx_busy  <= 1'b0;
                                rx_state <= RX_IDLE;
                            end
                        end else begin
                            rx_sample_cnt <= rx_sample_cnt + 4'd1;
                        end
                    end
                end

                RX_DATA: begin
                    if (sample_tick) begin
                        if (rx_sample_cnt == 4'd15) begin
                            // Sample at bit center
                            rx_shift_reg  <= {rx_in_sync, rx_shift_reg[7:1]};
                            rx_sample_cnt <= 4'd0;
                            if (rx_bit_cnt == 4'd7) begin
                                rx_state <= RX_STOP;
                            end else begin
                                rx_bit_cnt <= rx_bit_cnt + 4'd1;
                            end
                        end else begin
                            rx_sample_cnt <= rx_sample_cnt + 4'd1;
                        end
                    end
                end

                RX_STOP: begin
                    if (sample_tick) begin
                        if (rx_sample_cnt == 4'd15) begin
                            // Sample stop bit
                            rx_data      <= rx_shift_reg;
                            rx_frame_err <= (rx_in_sync == 1'b0) ? 1'b1 : 1'b0;
                            rx_valid     <= 1'b1;
                            rx_busy      <= 1'b0;
                            rx_state     <= RX_IDLE;
                        end else begin
                            rx_sample_cnt <= rx_sample_cnt + 4'd1;
                        end
                    end
                end

                default: begin
                    rx_busy  <= 1'b0;
                    rx_state <= RX_IDLE;
                end
            endcase
        end
    end

endmodule
