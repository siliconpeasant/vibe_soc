tclmode
# Native IEEE 1801 CLP check for source RTL against the canonical UPF.

proc env_required {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    puts stderr "UPF_CLP_FATAL: required environment variable '$name' is unset"
    exit 2
  }
  return $::env($name)
}
proc fatal {message} { puts stderr "UPF_CLP_FATAL: $message"; exit 2 }
proc require_file {path} {
  if {![file exists $path] || [file size $path] == 0} {
    fatal "missing or empty input: $path"
  }
}
proc split_words {value} {
  if {$value eq ""} { return {} }
  return [regexp -all -inline {\S+} $value]
}
proc logic_rtl_files {filelist project_root} {
  set fd [open $filelist r]
  set result {}
  foreach raw_line [split [read $fd] "\n"] {
    set line [string trim $raw_line]
    if {$line eq "" || [string match "#*" $line] || [string match "//*" $line]} {
      continue
    }
    set line [string map [list {$SOC} $project_root] $line]
    if {[regexp {upf_dc_demo_(pll_macro|sram_16x8|pad_in|pad_out)\.v$} $line]} {
      continue
    }
    require_file $line
    lappend result $line
  }
  close $fd
  if {[llength $result] == 0} { fatal "no synthesizable RTL files in $filelist" }
  return $result
}

set top [env_required CLP_TOP]
set project_root [env_required PROJECT_ROOT]
set filelist [env_required CLP_RTL_FILELIST]
set upf [env_required CLP_UPF]
set library_files [split_words [env_required CLP_LIB_FILES]]
set run_dir [env_required CLP_RUN_DIR]

if {$top ne "upf_dc_demo"} { fatal "expected top upf_dc_demo, got '$top'" }
foreach path [concat [list $filelist $upf] $library_files] { require_file $path }
file mkdir $run_dir
set rtl_files [logic_rtl_files $filelist $project_root]

usage -auto -elapse
set_lowpower_option -native_1801
set_lowpower_option -golden_analysis_style pre_synthesis

if {[catch {read_library -liberty -lp $library_files} message]} {
  fatal "low-power Liberty read failed: $message"
}
if {[catch {read_design -v2k $rtl_files -noelaborate} message]} {
  fatal "RTL read failed: $message"
}
if {[catch {elaborate_design -root $top} message]} {
  fatal "RTL elaboration failed: $message"
}
report_design_data > [file join $run_dir design_data.rpt]
report_black_box -class Full > [file join $run_dir black_boxes.rpt]

# The canonical file declares UPF 2.1. Native 1801 read immediately executes
# critical and structural RTL/power-intent consistency checks.
if {[catch {read_power_intent -1801 $upf -version 2.1} message]} {
  fatal "native 1801 read/check failed: $message"
}

report_rule_check -1801 -summary -occurrence_count > [file join $run_dir rules_1801_summary.rpt]
report_rule_check -1801 -error -status fail -summary -occurrence_count > [file join $run_dir rules_1801_errors.rpt]
report_rule_check -1801 -error -status fail -summary -xml [file join $run_dir rules_1801_errors.xml]
report_power_intent -verbose > [file join $run_dir power_intent.rpt]
report_lowpower_info -strategy * -all -verbose > [file join $run_dir lowpower.rpt]

foreach report_name {
  design_data.rpt black_boxes.rpt rules_1801_summary.rpt
  rules_1801_errors.rpt power_intent.rpt lowpower.rpt
} {
  require_file [file join $run_dir $report_name]
}

# The registered MCP wrapper is the sole PASS authority. It validates the
# generated XML and text reports fail-closed before emitting UPF_CLP_PASS.
puts "UPF_CLP_REPORTS_READY top=$top native_1801=2.1 analysis=pre_synthesis"
exit -force 0
