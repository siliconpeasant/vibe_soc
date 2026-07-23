# Post-route STA signoff helper for stories260k (OpenROAD + SPEF).
# Usage:
#   STA_WORK_HOME=<project>/pd/openroad/work_local \
#   SILICON_CREW_ORFS_DIR=<orfs>/flow \
#   openroad -exit pd/openroad/nangate45/stories260k/sta_signoff.tcl
#
# Env:
#   STA_WORK_HOME     ORFS work home (required if [info script] path is unreliable)
#   STA_VARIANT       FLOW_VARIANT (default: base)
#   STA_DESIGN_DIR    this design directory (default: dirname of this script if available)
#   SILICON_CREW_ORFS_DIR  ORFS flow dir for nangate45 liberty

# Prefer env for robust pathing under OpenROAD -exit
if { [info exists ::env(STA_DESIGN_DIR)] && $::env(STA_DESIGN_DIR) ne "" } {
  set design_dir [file normalize $::env(STA_DESIGN_DIR)]
} elseif { [info script] ne "" } {
  set design_dir [file normalize [file dirname [info script]]]
} else {
  puts "ERROR: set STA_DESIGN_DIR to pd/openroad/nangate45/stories260k"
  exit 1
}

if { [info exists ::env(STA_WORK_HOME)] && $::env(STA_WORK_HOME) ne "" } {
  set work_home [file normalize $::env(STA_WORK_HOME)]
} else {
  set work_home [file normalize [file join $design_dir ../../work_local]]
}

if { [info exists ::env(STA_VARIANT)] && $::env(STA_VARIANT) ne "" } {
  set variant $::env(STA_VARIANT)
} else {
  set variant base
}

if { [info exists ::env(SILICON_CREW_ORFS_DIR)] && $::env(SILICON_CREW_ORFS_DIR) ne "" } {
  set orfs_flow [file normalize $::env(SILICON_CREW_ORFS_DIR)]
} else {
  set orfs_flow /project/xuanwu9000/user/silicon/OpenROAD-flow-scripts-master/flow
}

set res [file join $work_home results nangate45 stories260k $variant]
set lib_nangate [file join $orfs_flow platforms nangate45 lib NangateOpenCellLibrary_typical.lib]
set lib_spm [file join $design_dir stories260k_spm.lib]
set odb [file join $res 6_final.odb]
set sdc [file join $res 6_final.sdc]
set spef [file join $res 6_final.spef]
set out_dir [file join $work_home reports nangate45 stories260k $variant]
file mkdir $out_dir

puts "STA signoff work=$work_home variant=$variant"
puts "  design_dir=$design_dir"
puts "  odb=$odb"
puts "  spef=$spef"
puts "  spm_lib=$lib_spm"

foreach f [list $lib_nangate $lib_spm $odb $sdc] {
  if { ![file exists $f] } {
    puts "ERROR: missing $f"
    exit 1
  }
}

read_liberty $lib_nangate
read_liberty $lib_spm
read_db $odb
read_sdc $sdc
if { [file exists $spef] } {
  read_spef $spef
} else {
  puts "WARN: no SPEF; using placement parasitics only"
  source [file join $orfs_flow platforms nangate45 setRC.tcl]
  estimate_parasitics -placement
}

set_propagated_clock [all_clocks]

puts "==== SETUP (max) top 5 ===="
report_checks -path_delay max -format end -group_count 5
puts "==== HOLD (min) top 10 ===="
report_checks -path_delay min -format end -group_count 10
puts "==== HOLD violators (slack_max 0) ===="
report_checks -path_delay min -format end -slack_max 0 -group_count 50
puts "==== SETUP WNS/TNS ===="
report_wns
report_tns
puts "==== max_slew / max_cap / max_fanout violators ===="
report_check_types -max_slew -max_cap -max_fanout -violators

set summary [file join $out_dir sta_signoff_summary.txt]
set fp [open $summary w]
puts $fp "stories260k post-route STA signoff"
puts $fp "odb: $odb"
puts $fp "spef: $spef"
puts $fp "spm_lib: $lib_spm"
close $fp

report_wns > [file join $out_dir sta_setup_wns.txt]
report_tns > [file join $out_dir sta_setup_tns.txt]
report_checks -path_delay min -format end -slack_max 0 -group_count 100 \
  > [file join $out_dir sta_hold_endpoints.txt]
report_checks -path_delay max -format end -group_count 10 \
  > [file join $out_dir sta_setup_endpoints.txt]
report_check_types -max_slew -max_cap -max_fanout -violators \
  > [file join $out_dir sta_drv_violators.txt]

puts "Wrote summary under $out_dir"
puts "==== DONE ===="
exit
