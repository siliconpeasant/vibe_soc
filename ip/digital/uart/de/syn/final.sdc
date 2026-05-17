#============================================================================
# SDC Constraints for uart
#============================================================================

# Clock definition (100MHz)
create_clock -period 10.0 [get_ports clk]

# Async reset: false path
set_false_path -from [get_ports rst_n]

# Input delays
set_input_delay -clock clk -max 2.0 [get_ports {tx_data[*] tx_valid rx_in baud_div[*]}]
set_input_delay -clock clk -min 0.5 [get_ports {tx_data[*] tx_valid rx_in baud_div[*]}]

# Output delays
set_output_delay -clock clk -max 2.0 [get_ports {tx_out tx_ready tx_busy tx_done rx_data[*] rx_valid rx_busy rx_frame_err}]
set_output_delay -clock clk -min 0.5 [get_ports {tx_out tx_ready tx_busy tx_done rx_data[*] rx_valid rx_busy rx_frame_err}]

# Set max delay for combinational paths (if any)
set_max_delay 10.0 -from [get_ports {tx_data[*] tx_valid rx_in baud_div[*]}] -to [get_ports {tx_out tx_ready tx_busy tx_done rx_data[*] rx_valid rx_busy rx_frame_err}]
