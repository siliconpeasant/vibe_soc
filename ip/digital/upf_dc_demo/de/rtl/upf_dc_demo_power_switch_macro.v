`ifndef SYNTHESIS
// Signal-only behavioral view. Supply transfer is defined by PSW_SW in UPF;
// the synthesis Liberty view adds VIN, VOUT, and VSS as pg_pin objects.
module upf_dc_demo_power_switch_macro (
    input wire en_i
);
  wire unused_en = en_i;
endmodule
`endif
