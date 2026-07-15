module upf_dc_demo_aon_ctrl (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       sw_power_req_i,
    input  wire [7:0] core_rsp_data_i,
    input  wire       core_rsp_valid_i,
    output reg        sw_en_o,
    output reg        sw_iso_n_o,
    output wire       traffic_enable_o,
    output reg  [7:0] rsp_data_o,
    output reg        rsp_valid_o
);
  localparam [2:0] ST_OFF     = 3'd0;
  localparam [2:0] ST_START_1 = 3'd1;
  localparam [2:0] ST_START_2 = 3'd2;
  localparam [2:0] ST_ON      = 3'd3;
  localparam [2:0] ST_STOP    = 3'd4;
  reg [2:0] state;

  assign traffic_enable_o = sw_en_o & sw_iso_n_o;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state       <= ST_OFF;
      sw_en_o     <= 1'b0;
      sw_iso_n_o  <= 1'b0;
      rsp_data_o  <= 8'h00;
      rsp_valid_o <= 1'b0;
    end else begin
      rsp_valid_o <= 1'b0;
      if (!sw_iso_n_o) begin
        rsp_data_o <= 8'h00;
      end else begin
        rsp_data_o  <= core_rsp_data_i;
        rsp_valid_o <= core_rsp_valid_i;
      end

      case (state)
        ST_OFF: begin
          sw_en_o    <= 1'b0;
          sw_iso_n_o <= 1'b0;
          if (sw_power_req_i) begin
            sw_en_o <= 1'b1;
            state   <= ST_START_1;
          end
        end
        ST_START_1: begin
          sw_iso_n_o <= 1'b0;
          if (!sw_power_req_i)
            state <= ST_STOP;
          else
            state <= ST_START_2;
        end
        ST_START_2: begin
          if (!sw_power_req_i)
            state <= ST_STOP;
          else begin
            sw_iso_n_o <= 1'b1;
            state      <= ST_ON;
          end
        end
        ST_ON: begin
          if (!sw_power_req_i) begin
            sw_iso_n_o <= 1'b0;
            state      <= ST_STOP;
          end
        end
        ST_STOP: begin
          sw_en_o    <= 1'b0;
          sw_iso_n_o <= 1'b0;
          state      <= ST_OFF;
        end
        default: begin
          state       <= ST_OFF;
          sw_en_o     <= 1'b0;
          sw_iso_n_o  <= 1'b0;
          rsp_data_o  <= 8'h00;
          rsp_valid_o <= 1'b0;
        end
      endcase
    end
  end
endmodule
