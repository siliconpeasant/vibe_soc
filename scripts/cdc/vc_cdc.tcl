# Unified VC Static CDC driver for vibe_soc modules.
# Required environment:
#   VC_CDC_FILELIST  Absolute RTL filelist generated as de/run/rtl.f.
#   VC_CDC_TOP       RTL top module.
#   VC_CDC_REPORT    Output detailed CDC report path.
#   VC_CDC_SUMMARY   Output summary CDC report path.

proc getenv_required {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    puts stderr "ERROR: required environment variable $name is not set"
    exit 2
  }
  return $::env($name)
}

proc getenv_default {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} {
    return $::env($name)
  }
  return $default_value
}

set filelist   [getenv_required VC_CDC_FILELIST]
set top        [getenv_required VC_CDC_TOP]
set report     [getenv_required VC_CDC_REPORT]
set summary    [getenv_required VC_CDC_SUMMARY]
set sdc        [getenv_default VC_CDC_SDC ""]
set setup      [getenv_default VC_CDC_SETUP ""]
set check_args [getenv_default VC_CDC_CHECK_ARGS ""]

if {![file exists $filelist]} {
  puts stderr "ERROR: VC_CDC_FILELIST does not exist: $filelist"
  exit 2
}
if {$sdc ne "" && ![file exists $sdc]} {
  puts stderr "ERROR: VC_CDC_SDC does not exist: $sdc"
  exit 2
}

file mkdir [file dirname $report]
file mkdir [file dirname $summary]

set search_path [getenv_default VC_CDC_SEARCH_PATH [file dirname $filelist]]
set link_library " "
set_app_var enable_cdc true

catch {set_app_var analyze_skip_translate_body true}
catch {set_app_var enable_exit_codes true}
catch {compress_hdl -enable}

puts "INFO: VC Static CDC filelist: $filelist"
puts "INFO: VC Static CDC top:      $top"
puts "INFO: VC Static CDC SDC:      $sdc"
puts "INFO: VC Static CDC report:   $report"
puts "INFO: VC Static CDC summary:  $summary"

set vcs_args [list -f $filelist]
analyze -format sverilog -vcs $vcs_args
elaborate $top

if {$setup ne "" && [file exists $setup]} {
  puts "INFO: Sourcing module VC CDC setup: $setup"
  source $setup
}

if {$sdc ne ""} {
  read_sdc $sdc
} else {
  puts "WARN: No VC_CDC_SDC provided; CDC checks may not infer intended clocks."
}

catch {configure_cdc_nff_sync -detect_full_chain true}

if {$check_args ne ""} {
  eval check_cdc $check_args
} else {
  check_cdc
}

report_cdc -file $summary
report_cdc -verbose -file $report
save_session

quit
