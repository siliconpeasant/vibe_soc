
# io_top constraint
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO0] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_GPIO1] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_CLK] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 2  -max -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay
set_input_delay 0.0   -min -clock [get_clocks {clk}]  [get_ports PAD_RST_N] -add_delay

set_input_transition -max 2.000 [get_ports {PAD_GPIO0}]
set_input_transition -min 2.000 [get_ports {PAD_GPIO0}]
set_input_transition -max 2.000 [get_ports {PAD_GPIO1}]
set_input_transition -min 2.000 [get_ports {PAD_GPIO1}]
set_input_transition -max 2.000 [get_ports {PAD_CLK}]
set_input_transition -min 2.000 [get_ports {PAD_CLK}]
set_input_transition -max 2.000 [get_ports {PAD_RST_N}]
set_input_transition -min 2.000 [get_ports {PAD_RST_N}]

set_load -pin_load -max 30 [get_ports {PAD_GPIO0}]
set_load -pin_load -min 30 [get_ports {PAD_GPIO0}]
set_load -pin_load -max 30 [get_ports {PAD_GPIO1}]
set_load -pin_load -min 30 [get_ports {PAD_GPIO1}]
set_load -pin_load -max 30 [get_ports {PAD_CLK}]
set_load -pin_load -min 30 [get_ports {PAD_CLK}]
set_load -pin_load -max 30 [get_ports {PAD_RST_N}]
set_load -pin_load -min 30 [get_ports {PAD_RST_N}]
