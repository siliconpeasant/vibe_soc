# OpenROAD constraints for vibe_soc_top
current_design vibe_soc_top

set clk_name core_clock
set clk_port_name clk
set clk_period 10
set clk_io_pct 0.2

set clk_port [get_ports $clk_port_name]
create_clock -name $clk_name -period $clk_period $clk_port

set non_clock_inputs [all_inputs -no_clocks]
set_input_delay [expr $clk_period * $clk_io_pct] -clock $clk_name $non_clock_inputs
set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_name [all_outputs]

set reset_port [get_ports -quiet rst_n]
if { [llength $reset_port] > 0 } {
  set_false_path -from $reset_port
}
