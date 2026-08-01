# Generic Design Compiler/Power Compiler UPF synthesis flow.

set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir .. tcl flow_common.tcl]
flow::set_fatal_prefix "DC_UPF_FATAL"

set top                [flow::env_required DC_TOP]
set filelist           [flow::env_required DC_FILELIST]
set sdc                [flow::env_required DC_SDC]
set upf_file           [flow::env_required DC_UPF]
set setup_tcl          [flow::env_or DC_SETUP_TCL ""]
set checks_tcl         [flow::env_or DC_UPF_CHECKS_TCL ""]
set work_dir           [flow::env_or DC_WORK_DIR "work"]
set report_dir         [flow::env_or DC_REPORT_DIR "reports"]
set output_dir         [flow::env_or DC_OUTPUT_DIR "outputs"]
set netlist            [flow::env_or DC_NETLIST "$output_dir/${top}_netlist.v"]
set ddc                [flow::env_or DC_DDC "$output_dir/${top}.ddc"]
set sdf                [flow::env_or DC_SDF "$output_dir/${top}.sdf"]
set sdc_out            [flow::env_or DC_SDC_OUT "$output_dir/${top}.sdc"]
set svf                [flow::env_or DC_SVF "$output_dir/${top}.svf"]
set upf_out            [flow::env_or DC_SAVED_UPF "$output_dir/${top}_synth.upf"]
set loaded_upf         [flow::env_or DC_LOADED_UPF "$report_dir/loaded_upf.pre_compile.upf"]
set timing_out         [flow::env_or DC_TIMING_REPORT "$report_dir/timing.rpt"]
set timing_summary_out [flow::env_or DC_TIMING_SUMMARY "$report_dir/timing_summary.rpt"]
set search_path_in     [flow::env_or DC_SEARCH_PATH ""]
set target_lib         [flow::env_or DC_TARGET_LIBRARY ""]
set link_lib           [flow::env_or DC_LINK_LIBRARY ""]
set symbol_lib         [flow::env_or DC_SYMBOL_LIBRARY ""]
set compile_ultra      [flow::env_or DC_COMPILE_ULTRA "1"]
set compile_options    [flow::env_or DC_COMPILE_OPTIONS ""]
set clock_gating       [flow::env_or DC_CLOCK_GATING "0"]
set max_cores          [flow::env_or DC_MAX_CORES "1"]
set rtl_define         [flow::env_or DC_RTL_DEFINE "SYNTHESIS"]

foreach path [list $filelist $sdc $upf_file] {
  flow::require_file $path
}
flow::source_optional $checks_tcl "DC_UPF_CHECKS_TCL"

file mkdir $work_dir
file mkdir $report_dir
file mkdir $output_dir
foreach stale [glob -nocomplain -directory $report_dir *] {
  file delete -force $stale
}
foreach stale [list $ddc $netlist $sdf $sdc_out $upf_out $svf $timing_out $timing_summary_out] {
  if {[file exists $stale]} {
    file delete -force $stale
  }
}

flow::require_command set_svf
if {[catch {set_svf $svf} message]} {
  flow::fatal "unable to enable Formality guidance output '$svf': $message"
}
define_design_lib WORK -path $work_dir
set alib_dir [file join $work_dir alib]
file mkdir $alib_dir
set_app_var alib_library_analysis_path $alib_dir
set_app_var hdlin_enable_upf_compatible_naming true
set_app_var verilogout_no_tri true
if {$max_cores ne ""} {
  set_host_options -max_cores $max_cores
}
set_app_var search_path [concat [get_app_var search_path] [flow::split_words $search_path_in]]
flow::source_optional $setup_tcl "DC_SETUP_TCL"
if {$target_lib ne ""} {
  set_app_var target_library [flow::split_words $target_lib]
}
set link_words [flow::split_words $link_lib]
if {[llength $link_words] > 0} {
  set_app_var link_library $link_words
} elseif {[llength [get_app_var target_library]] > 0} {
  set_app_var link_library [concat [list *] [get_app_var target_library]]
}
if {$symbol_lib ne ""} {
  set_app_var symbol_library [flow::split_words $symbol_lib]
}

puts "DC UPF top:      $top"
puts "DC RTL filelist: $filelist"
puts "DC UPF input:    $upf_file"
puts "DC saved UPF:    $upf_out"
puts "DC reports:      $report_dir"

# rtl.f is the single reviewed logic manifest for synthesis, Formality, and CLP.
set analyze_options "-f $filelist"
if {$rtl_define ne ""} {
  set analyze_options "+define+$rtl_define $analyze_options"
}
analyze -format sverilog -vcs $analyze_options
elaborate $top
current_design $top
link
uniquify
flow::run_hook dc_upf_post_elaborate

flow::require_command load_upf
set load_status [catch {
  redirect -tee -variable load_transcript {load_upf $upf_file}
} load_message]
if {$load_status} {
  flow::fatal "load_upf failed: $load_message"
}
set load_fd [open [file join $report_dir load_upf_transcript.rpt] w]
puts $load_fd $load_transcript
close $load_fd
if {[regexp -nocase {(^|\n)Error:|UPF-048|DC_UPF_FATAL} $load_transcript]} {
  flow::fatal "load_upf transcript contains an error diagnostic"
}
save_upf -full_upf $loaded_upf
flow::require_file $loaded_upf
flow::run_hook dc_upf_post_load_upf

read_sdc $sdc
set_fix_multiple_port_nets -all -buffer_constants
flow::required_report [file join $report_dir check_design.pre_compile.rpt] {check_design}
flow::required_report [file join $report_dir mv_check.pre_compile.rpt] {check_mv_design -verbose}
flow::required_report [file join $report_dir power_domains.pre_compile.rpt] {report_power_domain}
flow::required_report [file join $report_dir supply_connectivity.pre_compile.rpt] {report_supply_net}
flow::run_hook dc_upf_pre_compile

set compile_command [list [expr {[flow::bool_enabled $compile_ultra] ? "compile_ultra" : "compile"}]]
if {[flow::bool_enabled $clock_gating] && [flow::bool_enabled $compile_ultra]} {
  lappend compile_command -gate_clock
}
foreach option [flow::split_words $compile_options] {
  lappend compile_command $option
}
set compile_status [catch {
  redirect -tee -variable compile_transcript {uplevel #0 $compile_command}
} compile_message]
if {$compile_status} {
  flow::fatal "[lindex $compile_command 0] failed: $compile_message"
}
set compile_fd [open [file join $report_dir compile_transcript.rpt] w]
puts $compile_fd $compile_transcript
close $compile_fd
if {[regexp -nocase {(^|\n)Error:} $compile_transcript]} {
  flow::fatal "compile transcript contains an error diagnostic"
}
link

flow::required_report [file join $report_dir check_design.rpt] {check_design}
flow::required_report [file join $report_dir mv_check.rpt] {check_mv_design -verbose}
flow::required_report [file join $report_dir power_domains.rpt] {report_power_domain}
flow::required_report [file join $report_dir supply_nets.rpt] {report_supply_net}
flow::required_report [file join $report_dir isolation.rpt] {report_isolation_cell}
flow::required_report [file join $report_dir level_shifters.rpt] {report_level_shifter}
flow::required_report [file join $report_dir qor.rpt] {report_qor}
flow::required_report [file join $report_dir area.rpt] {report_area -hierarchy}
flow::required_report $timing_summary_out {report_qor}
flow::required_report $timing_out {report_timing -max_paths 20 -transition_time -nets -attributes}
flow::required_report [file join $report_dir constraints.rpt] {report_constraint -all_violators}
flow::run_hook dc_upf_post_compile

change_names -rules verilog -hierarchy
write_file -format ddc -hierarchy -output $ddc
write_file -format verilog -hierarchy -output $netlist
write_sdc $sdc_out
write_sdf $sdf
save_upf -full_upf $upf_out
if {[catch {set_svf -off} message]} {
  flow::fatal "unable to close Formality guidance output '$svf': $message"
}
foreach path [list $ddc $netlist $sdf $sdc_out $upf_out $svf $timing_out $timing_summary_out] {
  flow::require_file $path
}
flow::run_hook dc_upf_post_write

puts "DC_UPF_OUTPUTS_READY top=$top netlist=$netlist saved_upf=$upf_out svf=$svf"
exit 0
