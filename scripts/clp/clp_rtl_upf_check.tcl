tclmode
# Generic native IEEE 1801 CLP check for source RTL against canonical UPF.

set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir .. tcl flow_common.tcl]
flow::set_fatal_prefix "UPF_CLP_FATAL"

set top             [flow::env_required CLP_TOP]
set project_root    [flow::env_required PROJECT_ROOT]
set filelist        [flow::env_required CLP_RTL_FILELIST]
set upf             [flow::env_required CLP_UPF]
set library_files   [flow::split_words [flow::env_required CLP_LIB_FILES]]
set run_dir         [flow::env_required CLP_RUN_DIR]
set upf_version     [flow::env_or CLP_UPF_VERSION "2.1"]
set analysis_style  [flow::env_or CLP_ANALYSIS_STYLE "pre_synthesis"]
set setup_hook      [flow::env_or CLP_SETUP_HOOK ""]
set rtl_define      [flow::env_or CLP_RTL_DEFINE "SYNTHESIS"]

foreach path [concat [list $filelist $upf] $library_files] {
  flow::require_file $path
}
file mkdir $run_dir
flow::require_filelist $filelist

usage -auto -elapse
set_lowpower_option -native_1801
set_lowpower_option -golden_analysis_style $analysis_style
flow::source_optional $setup_hook "CLP_SETUP_HOOK"

if {[catch {read_library -liberty -lp $library_files} message]} {
  flow::fatal "low-power Liberty read failed: $message"
}
set read_args [list -v2k]
if {$rtl_define ne ""} {
  lappend read_args -define $rtl_define
}
# Keep rtl.f as the single tool-native manifest. Conformal interprets supported
# +incdir, -y, -v, define, and source entries through its -f adapter.
lappend read_args -f $filelist -noelaborate
if {[catch {read_design {*}$read_args} message]} {
  flow::fatal "RTL read failed: $message"
}
if {[catch {elaborate_design -root $top} message]} {
  flow::fatal "RTL elaboration failed: $message"
}
report_design_data > [file join $run_dir design_data.rpt]
report_black_box -class Full > [file join $run_dir black_boxes.rpt]

if {[catch {read_power_intent -1801 $upf -version $upf_version} message]} {
  flow::fatal "native 1801 read/check failed: $message"
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
  flow::require_file [file join $run_dir $report_name]
}

puts "UPF_CLP_REPORTS_READY top=$top native_1801=$upf_version analysis=$analysis_style"
exit -force 0
