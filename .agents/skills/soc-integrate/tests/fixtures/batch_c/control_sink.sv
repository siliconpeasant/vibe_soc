module control_sink(input control_pkg::enable_t enable_i, output logic enabled_o);
    assign enabled_o = (enable_i == control_pkg::Enabled) & control_pkg::Wide[0];
endmodule
