# Design-level GRT prep: keep ORFS 2024 compat, then free more global-routing
# capacity so hard-congestion hangs are avoidable.
# Prefer PROJECT_ROOT; else resolve relative to this design directory.
if { [info exists ::env(PROJECT_ROOT)] && $::env(PROJECT_ROOT) ne "" } {
  source [file join $::env(PROJECT_ROOT) pd/openroad/local/orfs_compat_2024.tcl]
} else {
  set _here [file dirname [file normalize [info script]]]
  set _proj [file normalize [file join $_here ../../../..]]
  source [file join $_proj pd/openroad/local/orfs_compat_2024.tcl]
}

# Platform default derates M2/M3 by 0.5 (~50% capacity). At high util that
# leaves residual overflow that breaks post-GRT -start_incremental steps.
if { [llength [info commands set_global_routing_layer_adjustment]] > 0 } {
  set_global_routing_layer_adjustment metal2-metal3 0.15
  set_global_routing_layer_adjustment metal4-metal10 0.10
  puts "Info: relaxed global routing layer adjustments for stories260k"
}
