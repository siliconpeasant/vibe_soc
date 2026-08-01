# Generic post-DC Formality equivalence flow. UPF is an optional paired input.

set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir .. tcl flow_common.tcl]
flow::set_fatal_prefix "FORMAL_FATAL"

set top                [flow::env_required FM_TOP]
set project_root       [flow::env_required PROJECT_ROOT]
set filelist           [flow::env_required FM_RTL_FILELIST]
set netlist            [flow::env_required FM_NETLIST]
set svf                [flow::env_required FM_SVF]
set library_dbs        [flow::split_words [flow::env_required FM_LIB_DB]]
set run_dir            [flow::env_required FM_RUN_DIR]
set reference_upf      [flow::env_or FM_REFERENCE_UPF ""]
set implementation_upf [flow::env_or FM_IMPLEMENTATION_UPF ""]
set setup_hook         [flow::env_or FM_SETUP_HOOK ""]
set rtl_define         [flow::env_or FM_RTL_DEFINE "SYNTHESIS"]

set use_upf [expr {$reference_upf ne "" || $implementation_upf ne ""}]
if {$use_upf && ($reference_upf eq "" || $implementation_upf eq "")} {
  flow::fatal "FM_REFERENCE_UPF and FM_IMPLEMENTATION_UPF must be set together"
}
foreach path [concat [list $filelist $netlist $svf] $library_dbs] {
  flow::require_file $path
}
if {$use_upf} {
  flow::require_file $reference_upf
  flow::require_file $implementation_upf
}
file mkdir $run_dir
flow::require_filelist $filelist

set synopsys_auto_setup true
set hdlin_library_autocorrect true
if {$use_upf} {
  set verification_force_upf_supplies_on false
}
if {[catch {set_svf $svf} message]} {
  flow::fatal "set_svf failed: $message"
}
if {[catch {read_db $library_dbs} message]} {
  flow::fatal "read_db failed: $message"
}
flow::source_optional $setup_hook "FM_SETUP_HOOK"

set reference_read_args [list -r]
if {$rtl_define ne ""} {
  lappend reference_read_args -define $rtl_define
}
# Keep rtl.f as the single tool-native manifest. Formality interprets supported
# +incdir, -y, -v, define, and source entries through its -f adapter.
lappend reference_read_args -f $filelist
if {[catch {read_verilog {*}$reference_read_args} message]} {
  flow::fatal "reference RTL read failed: $message"
}
if {[catch {set_top r:/WORK/$top} message]} {
  flow::fatal "reference set_top failed: $message"
}
if {$use_upf && [catch {load_upf -r $reference_upf} message]} {
  flow::fatal "reference load_upf failed: $message"
}

if {[catch {read_verilog -i $netlist} message]} {
  flow::fatal "implementation netlist read failed: $message"
}
if {[catch {set_top i:/WORK/$top} message]} {
  flow::fatal "implementation set_top failed: $message"
}
if {$use_upf && [catch {load_upf -i $implementation_upf} message]} {
  flow::fatal "implementation load_upf failed: $message"
}

flow::required_report [file join $run_dir library_defects.rpt] {report_libraries -defects errors}
if {$use_upf} {
  flow::required_report [file join $run_dir upf_reference.rpt] {report_upf -r -verbose}
  flow::required_report [file join $run_dir upf_implementation.rpt] {report_upf -i -verbose}
}
flow::required_report [file join $run_dir setup_status.rpt] {report_setup_status -all}

set match_result 0
if {[catch {redirect -file [file join $run_dir match_status.rpt] {
  set match_result [match]
  report_unmatched_points
}} message]} {
  flow::fatal "match failed to run: $message"
}
flow::require_file [file join $run_dir match_status.rpt]
if {!$match_result} {
  flow::fatal "Formality match returned failure"
}

set verify_result 0
if {[catch {set verify_result [verify]} message]} {
  flow::fatal "verify failed to run: $message"
}
flow::required_report [file join $run_dir verification_status.rpt] {report_status -last -short}
set verification_fd [open [file join $run_dir verification_status.rpt] a]
puts $verification_fd "VERIFICATION_STATUS=$verification_status"
close $verification_fd
if {!$verify_result || $verification_status ne "SUCCEEDED"} {
  flow::fatal "verification did not succeed: result=$verify_result status=$verification_status"
}

set formal_mode [expr {$use_upf ? "upf" : "plain"}]
puts "FORMAL_REPORTS_READY top=$top mode=$formal_mode status=$verification_status"
exit 0
