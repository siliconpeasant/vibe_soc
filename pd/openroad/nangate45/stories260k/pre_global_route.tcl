# Design-level GRT prep: keep ORFS 2024 compat, then free more global-routing
# capacity so hard-congestion hangs are avoidable.
# Resolve compat script robustly: OpenROAD's [info script] is unreliable when
# this file is sourced from ORFS (cwd is the ORFS flow dir).
set _compat ""
if { [info exists ::env(STORIES260K_ORFS_COMPAT)] &&
     $::env(STORIES260K_ORFS_COMPAT) ne "" &&
     [file exists $::env(STORIES260K_ORFS_COMPAT)] } {
  set _compat $::env(STORIES260K_ORFS_COMPAT)
} elseif { [info exists ::env(PRE_GLOBAL_ROUTE_TCL)] &&
           $::env(PRE_GLOBAL_ROUTE_TCL) ne "" } {
  set _here [file dirname [file normalize $::env(PRE_GLOBAL_ROUTE_TCL)]]
  set _compat [file normalize [file join $_here ../../local/orfs_compat_2024.tcl]]
}
if { $_compat eq "" || ![file exists $_compat] } {
  error "missing ORFS compat script (set STORIES260K_ORFS_COMPAT): $_compat"
}
source $_compat

# Platform default derates M2/M3 by 0.5 (~50% capacity). At high util that
# leaves residual overflow that breaks post-GRT -start_incremental steps.
if { [llength [info commands set_global_routing_layer_adjustment]] > 0 } {
  set_global_routing_layer_adjustment metal2-metal3 0.15
  set_global_routing_layer_adjustment metal4-metal10 0.10
  puts "Info: relaxed global routing layer adjustments for stories260k"
}
