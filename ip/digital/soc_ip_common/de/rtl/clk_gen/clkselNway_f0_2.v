module clkselNway_f0_2 (
    input  wire        clk0,
    input  wire        clk1,

    input  wire [1:0]  clksel,
    output wire [1:0]  select_cur,
    input  wire [1:0]  dftclksel,

    input  wire        resetn,

    input  wire        dftclkselen,
    input  wire        dftrstdisable,

    output wire        selected_clk
);

    //=========================================================================
    // Local parameters
    //=========================================================================
    localparam CLK0_ON  = 1'b0;
    localparam CLK0_OFF = 1'b1;
    localparam CLK1_ON  = 1'b0;
    localparam CLK1_OFF = 1'b1;

    //=========================================================================
    // Internal signals
    //=========================================================================
    // Reset sync
    wire               resetn_sync_clk0;
    wire               resetn_sync_clk1;

    // clk0 domain
    wire [1:0]         clk0selsync;
    reg  [1:0]         clk0selsync_valid;
    wire               clk1offclk0sync;
    reg                clk0state;
    reg                clk0nextstate;
    wire               iclk0off;
    reg                iclk0off_delay;

    // clk1 domain
    wire [1:0]         clk1selsync;
    reg  [1:0]         clk1selsync_valid;
    wire               clk0offclk1sync;
    reg                clk1state;
    reg                clk1nextstate;
    wire               iclk1off;
    reg                iclk1off_delay;

    // off status
    wire               clk0off;
    wire               clk0off_delay;
    wire               clk1off;
    wire               clk1off_delay;

    // clkgate control
    reg                nclk0off;
    reg                nclk1off;

    // gated clocks
    wire               iclk0;
    wire               iclk1;

    // select status
    wire [1:0]         iselect_cur;

    //=========================================================================
    // clk0 domain: reset synchronization
    //=========================================================================
    clkselNway_f0_rstsync_2 u_clkselNway_f0_rstsync_clk0(
        .clk            (clk0),
        .resetn_async   (resetn),
        .resetn_sync    (resetn_sync_clk0),
        .dftrstdisable  (dftrstdisable)
    );

    //=========================================================================
    // clk0 domain: clksel CDC sync
    //=========================================================================
    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_select0clk0(
        .clk            (clk0),
        .nreset         (resetn_sync_clk0),
        .d_async        (clksel[0]),
        .q              (clk0selsync[0])
    );

    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_select1clk0(
        .clk            (clk0),
        .nreset         (resetn_sync_clk0),
        .d_async        (clksel[1]),
        .q              (clk0selsync[1])
    );

    //=========================================================================
    // clk0 domain: valid decode
    //=========================================================================
    always @(clk0selsync)
    begin
        case ({clk0selsync})
        2'd1:    clk0selsync_valid = clk0selsync;
        2'd2:    clk0selsync_valid = clk0selsync;
        default: clk0selsync_valid = 2'd0;
        endcase
    end

    //=========================================================================
    // clk0 domain: clk1 off status CDC sync
    //=========================================================================
    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_clk1offclk0(
        .clk            (clk0),
        .nreset         (resetn_sync_clk0),
        .d_async        (clk1off_delay),
        .q              (clk1offclk0sync)
    );

    //=========================================================================
    // clk0 domain: state machine
    //=========================================================================
    always @(posedge clk0 or negedge resetn_sync_clk0)
    begin
        if (!resetn_sync_clk0)
            clk0state <= CLK0_OFF;
        else
            clk0state <= clk0nextstate;
    end

    always @(clk0selsync_valid or clk1offclk0sync or clk0state)
    begin
        clk0nextstate = clk0state;

        case (clk0state)
        CLK0_OFF:
            if ((clk1offclk0sync == 1'b1) &&
                (clk0selsync_valid == 2'd1))
                clk0nextstate = CLK0_ON;
        CLK0_ON:
            if (clk0selsync_valid != 2'd1)
                clk0nextstate = CLK0_OFF;
        endcase
    end

    assign iclk0off = (clk0state == CLK0_ON) ? 1'b0 : 1'b1;

    //=========================================================================
    // clk0 domain: off delay
    //=========================================================================
    always @(posedge clk0 or negedge resetn_sync_clk0)
    begin
        if (!resetn_sync_clk0)
            iclk0off_delay <= 1'b1;
        else
            iclk0off_delay <= iclk0off;
    end

    //=========================================================================
    // clk1 domain: reset synchronization
    //=========================================================================
    clkselNway_f0_rstsync_2 u_clkselNway_f0_rstsync_clk1(
        .clk            (clk1),
        .resetn_async   (resetn),
        .resetn_sync    (resetn_sync_clk1),
        .dftrstdisable  (dftrstdisable)
    );

    //=========================================================================
    // clk1 domain: clksel CDC sync
    //=========================================================================
    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_select0clk1(
        .clk            (clk1),
        .nreset         (resetn_sync_clk1),
        .d_async        (clksel[0]),
        .q              (clk1selsync[0])
    );

    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_select1clk1(
        .clk            (clk1),
        .nreset         (resetn_sync_clk1),
        .d_async        (clksel[1]),
        .q              (clk1selsync[1])
    );

    //=========================================================================
    // clk1 domain: valid decode
    //=========================================================================
    always @(clk1selsync)
    begin
        case ({clk1selsync})
        2'd1:    clk1selsync_valid = clk1selsync;
        2'd2:    clk1selsync_valid = clk1selsync;
        default: clk1selsync_valid = 2'd0;
        endcase
    end

    //=========================================================================
    // clk1 domain: clk0 off status CDC sync
    //=========================================================================
    clkselNway_f0_cdc_capt_sync_2 u_clkselNway_f0_cdc_capt_sync_clk0offclk1(
        .clk            (clk1),
        .nreset         (resetn_sync_clk1),
        .d_async        (clk0off_delay),
        .q              (clk0offclk1sync)
    );

    //=========================================================================
    // clk1 domain: state machine
    //=========================================================================
    always @(posedge clk1 or negedge resetn_sync_clk1)
    begin
        if (!resetn_sync_clk1)
            clk1state <= CLK1_OFF;
        else
            clk1state <= clk1nextstate;
    end

    always @(clk1selsync_valid or clk0offclk1sync or clk1state)
    begin
        clk1nextstate = clk1state;

        case (clk1state)
        CLK1_OFF:
            if ((clk0offclk1sync == 1'b1) &&
                (clk1selsync_valid == 2'd2))
                clk1nextstate = CLK1_ON;
        CLK1_ON:
            if (clk1selsync_valid != 2'd2)
                clk1nextstate = CLK1_OFF;
        endcase
    end

    assign iclk1off = (clk1state == CLK1_ON) ? 1'b0 : 1'b1;

    //=========================================================================
    // clk1 domain: off delay
    //=========================================================================
    always @(posedge clk1 or negedge resetn_sync_clk1)
    begin
        if (!resetn_sync_clk1)
            iclk1off_delay <= 1'b1;
        else
            iclk1off_delay <= iclk1off;
    end

    //=========================================================================
    // off status assignment
    //=========================================================================
    assign clk0off       = iclk0off;
    assign clk0off_delay = iclk0off_delay;
    assign clk1off       = iclk1off;
    assign clk1off_delay = iclk1off_delay;

    //=========================================================================
    // clkgate control (DFT bypass)
    //=========================================================================
    always @(dftclksel or clk0off or clk1off or dftclkselen)
    begin
        if (dftclkselen)
        begin
            {nclk1off, nclk0off} = dftclksel;
        end
        else
        begin
            nclk0off = ~clk0off;
            nclk1off = ~clk1off;
        end
    end

    //=========================================================================
    // Clock gating
    //=========================================================================
    clkselNway_f0_clkgate_2 u_clkselNway_f0_clkgate_clk_0(
        .clk_in         (clk0),
        .enable         (nclk0off),
        .clk_out        (iclk0),
        .dftcgen        (1'b0)
    );

    clkselNway_f0_clkgate_2 u_clkselNway_f0_clkgate_clk_1(
        .clk_in         (clk1),
        .enable         (nclk1off),
        .clk_out        (iclk1),
        .dftcgen        (1'b0)
    );

    //=========================================================================
    // Clock output mux
    // 注：原代码此处存在 `ifdef / `else / `endif 条件编译，
    //     因截图未包含前部，此处仅保留实际功能逻辑（clkor2 实现）。
    //     若需恢复条件编译，请根据原始宏定义补充 `ifdef 分支。
    //=========================================================================
    clkselNway_f0_clkor2_2 u_clkoutor2(
        .clk0_in        (iclk0),
        .clk1_in        (iclk1),
        .clk_out        (selected_clk)
    );

    //=========================================================================
    // Select status output
    //=========================================================================
    assign iselect_cur = {
        ~iclk1off_delay,
        ~iclk0off_delay
    };

    assign select_cur = iselect_cur;

endmodule
