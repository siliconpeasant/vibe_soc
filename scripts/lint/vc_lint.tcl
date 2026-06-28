# Unified VC Static lint driver for vibe_soc modules.
# Required environment:
#   VC_LINT_FILELIST  Absolute RTL filelist generated as de/run/rtl.f.
#   VC_LINT_TOP       RTL top module.
#   VC_LINT_REPORT    Output report path.

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

set filelist [getenv_required VC_LINT_FILELIST]
set top      [getenv_required VC_LINT_TOP]
set report   [getenv_required VC_LINT_REPORT]
set setup    [getenv_default VC_LINT_SETUP ""]
set rules    [getenv_default VC_LINT_RULES ""]

if {![file exists $filelist]} {
  puts stderr "ERROR: VC_LINT_FILELIST does not exist: $filelist"
  exit 2
}

file mkdir [file dirname $report]

set search_path [getenv_default VC_LINT_SEARCH_PATH [file dirname $filelist]]
set link_library " "
set enable_lang_checker true
set synth_preserve_sequential true

catch {set_app_var sync_reset_signal_threshold 0}
catch {set_app_var analyze_skip_translate_body true}
catch {set_app_var enable_exit_codes true}
catch {compress_hdl -enable}

puts "INFO: VC Static lint filelist: $filelist"
puts "INFO: VC Static lint top:      $top"
puts "INFO: VC Static lint report:   $report"

set vcs_args [list -f $filelist]
analyze -format sverilog -vcs $vcs_args
elaborate $top

if {$setup ne "" && [file exists $setup]} {
  puts "INFO: Sourcing module VC lint setup: $setup"
  source $setup
}

if {$rules ne "" && [file exists $rules]} {
  puts "INFO: Sourcing project VC lint rules: $rules"
  source $rules
}

if {[info exists ::env(VC_LINT_ENABLE_TAGS)] && $::env(VC_LINT_ENABLE_TAGS) ne ""} {
  foreach tag [split [string map {"," " "} $::env(VC_LINT_ENABLE_TAGS)]] {
    if {$tag ne ""} {
      configure_hdl_tag -enable -tag $tag
    }
  }
}

set tag_report [file join [file dirname $report] vc_lint_tags.rpt]
redirect -file $tag_report {configure_hdl_tag -all -verbose}
puts "INFO: VC Static lint tag report: $tag_report"

check_hdl -lang
check_hdl -structure
report_hdl -file $report -verbose
save_session

quit
