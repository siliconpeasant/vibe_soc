//============================================================================
// Module     : spi
// Function   : APB3 SPI Master controller with CPOL/CPHA config, programmable
//              baud rate, 4~16 bit frame length, 8-depth TX/RX FIFOs,
//              auto/manual CS management, and 5 interrupt sources.
// Author     : soc-rtl-designer
// Version    : 1.0
//============================================================================

`timescale 1ns / 1ps

module spi (
    // System
    input  wire        pclk,
    input  wire        preset_n,

    // APB slave interface
    input  wire [11:0] paddr,
    input  wire [31:0] pwdata,
    output reg  [31:0] prdata,
    input  wire        pwrite,
    input  wire        psel,
    input  wire        penable,

    // SPI interface
    output reg         sclk,
    output reg         mosi,
    input  wire        miso,
    output reg  [3:0]  cs_n,

    // Interrupt
    output wire        irq
);

    //========================================================================
    // Parameters
    //========================================================================
    localparam DATA_WIDTH     = 16;
    localparam FIFO_DEPTH     = 8;
    localparam FIFO_CNT_WIDTH = 4;
    localparam APB_ADDR_WIDTH = 12;
    localparam APB_DATA_WIDTH = 32;
    localparam NUM_SLAVES     = 4;
    localparam SPI_DIV_WIDTH  = 16;

    // Register address offsets
    localparam ADDR_CTRL   = 8'h00;
    localparam ADDR_STATUS = 8'h04;
    localparam ADDR_BAUD   = 8'h08;
    localparam ADDR_TXDATA = 8'h0C;
    localparam ADDR_RXDATA = 8'h10;
    localparam ADDR_IE     = 8'h14;
    localparam ADDR_IS     = 8'h18;
    localparam ADDR_FRAME  = 8'h1C;

    // SPI state encoding
    localparam SPI_IDLE      = 3'b000;
    localparam SPI_CS_SETUP  = 3'b001;
    localparam SPI_TRANSFER  = 3'b010;
    localparam SPI_CS_HOLD   = 3'b011;
    localparam SPI_DONE      = 3'b100;

    //========================================================================
    // Registers
    //========================================================================
    // CTRL register
    reg        ctrl_en;
    reg        ctrl_cpol;
    reg        ctrl_cpha;
    reg        ctrl_cs_manual;
    reg        ctrl_cs_val;
    reg [2:0]  ctrl_slave_sel;

    // BAUD register
    reg [SPI_DIV_WIDTH-1:0] baud_spi_div;

    // FRAME register
    reg [4:0]  frame_frame_len;
    reg [7:0]  frame_cs_setup;
    reg [7:0]  frame_cs_hold;

    // IE register
    reg ie_tx_empty;
    reg ie_rx_full;
    reg ie_tx_underrun;
    reg ie_rx_overrun;
    reg ie_transfer_done;

    // IS register (RW1C)
    reg is_tx_empty;
    reg is_rx_full;
    reg is_tx_underrun;
    reg is_rx_overrun;
    reg is_transfer_done;

    //========================================================================
    // Internal Signals (declared early for iverilog compatibility)
    //========================================================================
    reg  [FIFO_CNT_WIDTH-1:0] tx_fifo_cnt;
    reg  [FIFO_CNT_WIDTH-1:0] rx_fifo_cnt;
    wire [DATA_WIDTH-1:0]     rx_fifo_rdata;
    wire                      tx_fifo_wr_err;
    wire                      rx_fifo_wr_err;
    reg                       transfer_done_event;
    reg                       busy;

    //========================================================================
    // APB Interface
    //========================================================================
    wire        apb_wr_en;
    wire        apb_rd_en;
    wire [7:0]  reg_addr;

    assign apb_wr_en = psel && penable && pwrite;
    assign apb_rd_en = psel && penable && (!pwrite);
    assign reg_addr  = paddr[7:0];

    //========================================================================
    // Register Write Logic
    //========================================================================
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            ctrl_en         <= 1'b0;
            ctrl_cpol       <= 1'b0;
            ctrl_cpha       <= 1'b0;
            ctrl_cs_manual  <= 1'b0;
            ctrl_cs_val     <= 1'b1;
            ctrl_slave_sel  <= 3'b0;
            baud_spi_div    <= {SPI_DIV_WIDTH{1'b0}};
            frame_frame_len <= 5'd8;
            frame_cs_setup  <= 8'd1;
            frame_cs_hold   <= 8'd1;
            ie_tx_empty     <= 1'b0;
            ie_rx_full      <= 1'b0;
            ie_tx_underrun  <= 1'b0;
            ie_rx_overrun   <= 1'b0;
            ie_transfer_done<= 1'b0;
        end else if (apb_wr_en) begin
            case (reg_addr)
                ADDR_CTRL: begin
                    ctrl_en        <= pwdata[0];
                    ctrl_cpol      <= pwdata[1];
                    ctrl_cpha      <= pwdata[2];
                    ctrl_cs_manual <= pwdata[3];
                    ctrl_cs_val    <= pwdata[4];
                    ctrl_slave_sel <= pwdata[7:5];
                end
                ADDR_BAUD: begin
                    baud_spi_div <= pwdata[SPI_DIV_WIDTH-1:0];
                end
                ADDR_TXDATA: begin
                    // Handled by TX FIFO logic
                end
                ADDR_IE: begin
                    ie_tx_empty      <= pwdata[0];
                    ie_rx_full       <= pwdata[1];
                    ie_tx_underrun   <= pwdata[2];
                    ie_rx_overrun    <= pwdata[3];
                    ie_transfer_done <= pwdata[4];
                end
                ADDR_FRAME: begin
                    frame_frame_len <= (pwdata[4:0] < 5'd4)  ? 5'd4 :
                                       (pwdata[4:0] > 5'd16) ? 5'd16 : pwdata[4:0];
                    frame_cs_setup  <= (pwdata[15:8] == 8'd0) ? 8'd1 : pwdata[15:8];
                    frame_cs_hold   <= (pwdata[23:16] == 8'd0) ? 8'd1 : pwdata[23:16];
                end
                default: ;
            endcase
        end
    end

    //========================================================================
    // IS Register Set Logic (interrupt events)
    //========================================================================
    wire tx_fifo_empty_d;
    wire tx_fifo_full_d;
    wire rx_fifo_empty_d;
    wire rx_fifo_full_d;

    // Edge detection for FIFO status changes
    reg  tx_fifo_empty_q;
    reg  rx_fifo_full_q;

    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            tx_fifo_empty_q <= 1'b1;
            rx_fifo_full_q  <= 1'b0;
        end else begin
            tx_fifo_empty_q <= tx_fifo_empty_d;
            rx_fifo_full_q  <= rx_fifo_full_d;
        end
    end

    wire tx_empty_event = tx_fifo_empty_q && (!tx_fifo_empty_d);
    wire rx_full_event  = (!rx_fifo_full_q) && rx_fifo_full_d;

    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            is_tx_empty      <= 1'b0;
            is_rx_full       <= 1'b0;
            is_tx_underrun   <= 1'b0;
            is_rx_overrun    <= 1'b0;
            is_transfer_done <= 1'b0;
        end else begin
            // Set by hardware events
            if (tx_empty_event)       is_tx_empty      <= 1'b1;
            if (rx_full_event)        is_rx_full       <= 1'b1;
            if (tx_fifo_wr_err)       is_tx_underrun   <= 1'b1;
            if (rx_fifo_wr_err)       is_rx_overrun    <= 1'b1;
            if (transfer_done_event)  is_transfer_done <= 1'b1;

            // Clear by W1C (only if not simultaneously set)
            if (apb_wr_en && (reg_addr == ADDR_IS)) begin
                if (pwdata[0] && (!tx_empty_event))      is_tx_empty      <= 1'b0;
                if (pwdata[1] && (!rx_full_event))       is_rx_full       <= 1'b0;
                if (pwdata[2] && (!tx_fifo_wr_err))      is_tx_underrun   <= 1'b0;
                if (pwdata[3] && (!rx_fifo_wr_err))      is_rx_overrun    <= 1'b0;
                if (pwdata[4] && (!transfer_done_event)) is_transfer_done <= 1'b0;
            end
        end
    end

    //========================================================================
    // Register Read Logic
    //========================================================================
    always @(*) begin
        prdata = 32'h00000000;
        if (apb_rd_en) begin
            case (reg_addr)
                ADDR_CTRL:   prdata = {24'b0, ctrl_slave_sel, 1'b0, ctrl_cs_val,
                                       ctrl_cs_manual, ctrl_cpha, ctrl_cpol, ctrl_en};
                ADDR_STATUS: prdata = {19'b0, rx_fifo_cnt, tx_fifo_cnt, 3'b0,
                                       busy, rx_fifo_full_d, rx_fifo_empty_d,
                                       tx_fifo_full_d, tx_fifo_empty_d};
                ADDR_BAUD:   prdata = {{(32-SPI_DIV_WIDTH){1'b0}}, baud_spi_div};
                ADDR_TXDATA: prdata = 32'h00000000;
                ADDR_RXDATA: prdata = {16'b0, rx_fifo_rdata};
                ADDR_IE:     prdata = {27'b0, ie_transfer_done, ie_rx_overrun,
                                       ie_tx_underrun, ie_rx_full, ie_tx_empty};
                ADDR_IS:     prdata = {27'b0, is_transfer_done, is_rx_overrun,
                                       is_tx_underrun, is_rx_full, is_tx_empty};
                ADDR_FRAME:  prdata = {8'b0, frame_cs_hold, frame_cs_setup, 3'b0, frame_frame_len};
                default:     prdata = 32'h00000000;
            endcase
        end
    end

    //========================================================================
    // Interrupt Output
    //========================================================================
    assign irq = (ie_tx_empty      & is_tx_empty)      |
                 (ie_rx_full       & is_rx_full)       |
                 (ie_tx_underrun   & is_tx_underrun)   |
                 (ie_rx_overrun    & is_rx_overrun)    |
                 (ie_transfer_done & is_transfer_done);

    //========================================================================
    // TX FIFO (8-depth, 16-bit wide)
    //========================================================================
    reg [DATA_WIDTH-1:0] tx_fifo_mem [0:FIFO_DEPTH-1];
    reg [FIFO_CNT_WIDTH-1:0] tx_fifo_wr_ptr;
    reg [FIFO_CNT_WIDTH-1:0] tx_fifo_rd_ptr;

    wire                 tx_fifo_wr_en;
    wire                 tx_fifo_rd_en;
    wire [DATA_WIDTH-1:0] tx_fifo_wdata;
    wire [DATA_WIDTH-1:0] tx_fifo_rdata;

    assign tx_fifo_empty_d = (tx_fifo_cnt == {FIFO_CNT_WIDTH{1'b0}});
    assign tx_fifo_full_d  = (tx_fifo_cnt == FIFO_DEPTH[FIFO_CNT_WIDTH-1:0]);

    assign tx_fifo_wr_en  = apb_wr_en && (reg_addr == ADDR_TXDATA);
    assign tx_fifo_wdata  = pwdata[DATA_WIDTH-1:0];
    assign tx_fifo_wr_err = tx_fifo_wr_en && tx_fifo_full_d;

    // TX FIFO write
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            tx_fifo_wr_ptr <= {FIFO_CNT_WIDTH{1'b0}};
        end else if (tx_fifo_wr_en && (!tx_fifo_full_d)) begin
            tx_fifo_mem[tx_fifo_wr_ptr[FIFO_CNT_WIDTH-2:0]] <= tx_fifo_wdata;
            tx_fifo_wr_ptr <= tx_fifo_wr_ptr + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
        end
    end

    // TX FIFO read
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            tx_fifo_rd_ptr <= {FIFO_CNT_WIDTH{1'b0}};
        end else if (tx_fifo_rd_en && (!tx_fifo_empty_d)) begin
            tx_fifo_rd_ptr <= tx_fifo_rd_ptr + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
        end
    end

    assign tx_fifo_rdata = tx_fifo_mem[tx_fifo_rd_ptr[FIFO_CNT_WIDTH-2:0]];

    // TX FIFO counter
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            tx_fifo_cnt <= {FIFO_CNT_WIDTH{1'b0}};
        end else begin
            case ({tx_fifo_wr_en && (!tx_fifo_full_d), tx_fifo_rd_en && (!tx_fifo_empty_d)})
                2'b01:   tx_fifo_cnt <= tx_fifo_cnt - {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
                2'b10:   tx_fifo_cnt <= tx_fifo_cnt + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
                default: tx_fifo_cnt <= tx_fifo_cnt;
            endcase
        end
    end

    //========================================================================
    // RX FIFO (8-depth, 16-bit wide)
    //========================================================================
    reg [DATA_WIDTH-1:0] rx_fifo_mem [0:FIFO_DEPTH-1];
    reg [FIFO_CNT_WIDTH-1:0] rx_fifo_wr_ptr;
    reg [FIFO_CNT_WIDTH-1:0] rx_fifo_rd_ptr;

    wire                 rx_fifo_wr_en;
    wire                 rx_fifo_rd_en;
    wire [DATA_WIDTH-1:0] rx_fifo_wdata;

    assign rx_fifo_empty_d = (rx_fifo_cnt == {FIFO_CNT_WIDTH{1'b0}});
    assign rx_fifo_full_d  = (rx_fifo_cnt == FIFO_DEPTH[FIFO_CNT_WIDTH-1:0]);

    assign rx_fifo_rd_en  = apb_rd_en && (reg_addr == ADDR_RXDATA);
    assign rx_fifo_wr_err = rx_fifo_wr_en && rx_fifo_full_d;

    // RX FIFO write
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            rx_fifo_wr_ptr <= {FIFO_CNT_WIDTH{1'b0}};
        end else if (rx_fifo_wr_en && (!rx_fifo_full_d)) begin
            rx_fifo_mem[rx_fifo_wr_ptr[FIFO_CNT_WIDTH-2:0]] <= rx_fifo_wdata;
            rx_fifo_wr_ptr <= rx_fifo_wr_ptr + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
        end
    end

    // RX FIFO read
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            rx_fifo_rd_ptr <= {FIFO_CNT_WIDTH{1'b0}};
        end else if (rx_fifo_rd_en && (!rx_fifo_empty_d)) begin
            rx_fifo_rd_ptr <= rx_fifo_rd_ptr + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
        end
    end

    assign rx_fifo_rdata = rx_fifo_mem[rx_fifo_rd_ptr[FIFO_CNT_WIDTH-2:0]];

    // RX FIFO counter
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            rx_fifo_cnt <= {FIFO_CNT_WIDTH{1'b0}};
        end else begin
            case ({rx_fifo_wr_en && (!rx_fifo_full_d), rx_fifo_rd_en && (!rx_fifo_empty_d)})
                2'b01:   rx_fifo_cnt <= rx_fifo_cnt - {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
                2'b10:   rx_fifo_cnt <= rx_fifo_cnt + {{(FIFO_CNT_WIDTH-1){1'b0}}, 1'b1};
                default: rx_fifo_cnt <= rx_fifo_cnt;
            endcase
        end
    end

    //========================================================================
    // Baud Rate Generator
    //========================================================================
    reg [SPI_DIV_WIDTH-1:0] baud_cnt;
    reg        sclk_tick;

    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            baud_cnt  <= {SPI_DIV_WIDTH{1'b0}};
            sclk_tick <= 1'b0;
        end else if (!ctrl_en) begin
            baud_cnt  <= {SPI_DIV_WIDTH{1'b0}};
            sclk_tick <= 1'b0;
        end else begin
            if (baud_cnt >= baud_spi_div) begin
                baud_cnt  <= {SPI_DIV_WIDTH{1'b0}};
                sclk_tick <= 1'b1;
            end else begin
                baud_cnt  <= baud_cnt + {{(SPI_DIV_WIDTH-1){1'b0}}, 1'b1};
                sclk_tick <= 1'b0;
            end
        end
    end

    //========================================================================
    // SPI Master State Machine & Shift Controller
    //========================================================================
    reg [2:0]  spi_state;
    reg [4:0]  bit_cnt;
    reg [DATA_WIDTH-1:0] tx_shift_reg;
    reg [DATA_WIDTH-1:0] rx_shift_reg;
    reg [7:0]  cs_setup_cnt;
    reg [7:0]  cs_hold_cnt;
    reg        sclk_int;

    // sclk edge detection
    wire sclk_rising  = sclk_tick && (!sclk_int);
    wire sclk_falling = sclk_tick && sclk_int;

    // Data change edge and sample edge based on CPOL/CPHA
    wire data_change_edge;
    wire data_sample_edge;

    // For CPOL=0,CPHA=0: change on falling, sample on rising
    // For CPOL=0,CPHA=1: change on rising, sample on falling
    // For CPOL=1,CPHA=0: change on rising, sample on falling
    // For CPOL=1,CPHA=1: change on falling, sample on rising
    assign data_change_edge = (ctrl_cpol ^ ctrl_cpha) ? sclk_rising : sclk_falling;
    assign data_sample_edge = (ctrl_cpol ^ ctrl_cpha) ? sclk_falling : sclk_rising;

    // TX FIFO read enable (load data into shift reg)
    assign tx_fifo_rd_en = (spi_state == SPI_IDLE) && ctrl_en && (!tx_fifo_empty_d) &&
                           (spi_state != SPI_CS_SETUP) && (spi_state != SPI_TRANSFER) &&
                           (spi_state != SPI_CS_HOLD) && (spi_state != SPI_DONE);

    // RX FIFO write enable (store received data)
    wire rx_fifo_wr_en_int = (spi_state == SPI_TRANSFER) && (bit_cnt == frame_frame_len) &&
                              data_sample_edge;
    assign rx_fifo_wr_en = rx_fifo_wr_en_int;
    assign rx_fifo_wdata = rx_shift_reg;

    // Main SPI state machine
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            spi_state           <= SPI_IDLE;
            bit_cnt             <= 5'd0;
            tx_shift_reg        <= {DATA_WIDTH{1'b0}};
            rx_shift_reg        <= {DATA_WIDTH{1'b0}};
            cs_setup_cnt        <= 8'd0;
            cs_hold_cnt         <= 8'd0;
            sclk_int            <= 1'b0;
            sclk                <= 1'b0;
            mosi                <= 1'b0;
            transfer_done_event <= 1'b0;
            busy                <= 1'b0;
        end else if (!ctrl_en) begin
            spi_state           <= SPI_IDLE;
            bit_cnt             <= 5'd0;
            tx_shift_reg        <= {DATA_WIDTH{1'b0}};
            rx_shift_reg        <= {DATA_WIDTH{1'b0}};
            cs_setup_cnt        <= 8'd0;
            cs_hold_cnt         <= 8'd0;
            sclk_int            <= ctrl_cpol;
            sclk                <= ctrl_cpol;
            mosi                <= 1'b0;
            transfer_done_event <= 1'b0;
            busy                <= 1'b0;
        end else begin
            transfer_done_event <= 1'b0;

            case (spi_state)
                SPI_IDLE: begin
                    sclk_int     <= ctrl_cpol;
                    sclk         <= ctrl_cpol;
                    bit_cnt      <= 5'd0;
                    cs_setup_cnt <= 8'd0;
                    cs_hold_cnt  <= 8'd0;
                    busy         <= 1'b0;

                    if (ctrl_en && (!tx_fifo_empty_d)) begin
                        // Load data from TX FIFO
                        tx_shift_reg <= tx_fifo_rdata;
                        mosi         <= tx_fifo_rdata[DATA_WIDTH-1];
                        busy         <= 1'b1;
                        spi_state    <= SPI_CS_SETUP;
                    end
                end

                SPI_CS_SETUP: begin
                    busy <= 1'b1;
                    if (sclk_tick) begin
                        if (cs_setup_cnt >= frame_cs_setup - 8'd1) begin
                            cs_setup_cnt <= 8'd0;
                            spi_state    <= SPI_TRANSFER;
                            // First edge: if CPHA=0, first edge is sample edge
                            // If CPHA=1, first edge is change edge
                            if (ctrl_cpha == 1'b0) begin
                                // CPHA=0: sample on first edge (rising if CPOL=0)
                                // Data already setup by mosi above
                            end
                        end else begin
                            cs_setup_cnt <= cs_setup_cnt + 8'd1;
                        end
                    end
                end

                SPI_TRANSFER: begin
                    busy <= 1'b1;
                    if (sclk_tick) begin
                        sclk_int <= (!sclk_int);
                        sclk     <= (!sclk_int);

                        if (data_change_edge) begin
                            // Shift out next bit (MSB first)
                            if (bit_cnt < frame_frame_len - 5'd1) begin
                                tx_shift_reg <= {tx_shift_reg[DATA_WIDTH-2:0], 1'b0};
                                mosi         <= tx_shift_reg[DATA_WIDTH-2];
                            end
                        end else if (data_sample_edge) begin
                            // Sample miso (MSB first)
                            rx_shift_reg <= {rx_shift_reg[DATA_WIDTH-2:0], miso};

                            if (bit_cnt >= frame_frame_len - 5'd1) begin
                                // Last bit sampled
                                bit_cnt <= 5'd0;
                                spi_state <= SPI_CS_HOLD;
                            end else begin
                                bit_cnt <= bit_cnt + 5'd1;
                            end
                        end
                    end
                end

                SPI_CS_HOLD: begin
                    busy <= 1'b1;
                    // Return sclk to idle state
                    sclk_int <= ctrl_cpol;
                    sclk     <= ctrl_cpol;

                    if (sclk_tick) begin
                        if (cs_hold_cnt >= frame_cs_hold - 8'd1) begin
                            cs_hold_cnt <= 8'd0;
                            spi_state   <= SPI_DONE;
                        end else begin
                            cs_hold_cnt <= cs_hold_cnt + 8'd1;
                        end
                    end
                end

                SPI_DONE: begin
                    busy                <= 1'b1;
                    transfer_done_event <= 1'b1;
                    spi_state           <= SPI_IDLE;
                end

                default: begin
                    spi_state <= SPI_IDLE;
                end
            endcase
        end
    end

    //========================================================================
    // CS Manager
    //========================================================================
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            cs_n <= 4'b1111;
        end else if (!ctrl_en) begin
            cs_n <= 4'b1111;
        end else if (ctrl_cs_manual) begin
            // Manual mode: software controls cs_n via ctrl_cs_val
            cs_n <= ctrl_cs_val ? 4'b1111 :
                    (ctrl_slave_sel[1:0] == 2'b00) ? 4'b1110 :
                    (ctrl_slave_sel[1:0] == 2'b01) ? 4'b1101 :
                    (ctrl_slave_sel[1:0] == 2'b10) ? 4'b1011 :
                                                     4'b0111;
        end else begin
            // Auto mode: assert during transfer
            case (spi_state)
                SPI_CS_SETUP, SPI_TRANSFER, SPI_CS_HOLD, SPI_DONE: begin
                    cs_n <= (ctrl_slave_sel[1:0] == 2'b00) ? 4'b1110 :
                            (ctrl_slave_sel[1:0] == 2'b01) ? 4'b1101 :
                            (ctrl_slave_sel[1:0] == 2'b10) ? 4'b1011 :
                                                             4'b0111;
                end
                default: begin
                    cs_n <= 4'b1111;
                end
            endcase
        end
    end

endmodule
