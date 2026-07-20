#============================================================================
# SDC Constraints for stories260k
#============================================================================

# 100 MHz decode clock target (Nangate 45nm open-PDK timing-closure goal);
# this constraint file alone is not timing-closure evidence.
create_clock -period 10.0 [get_ports clk]
