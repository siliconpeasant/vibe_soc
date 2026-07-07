#============================================================================
# SDC Constraints for npu
#============================================================================

# Simple integration clock constraint only; this is not a timing-closure report.
create_clock -period 10.0 [get_ports clk]
