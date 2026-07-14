# Licensed DC/Power Compiler driver for the teaching-only two-domain demo.

proc env_or {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} { return $::env($name) }
  return $default_value
}
proc fatal {message} { puts stderr "UPF_DC_DEMO_FATAL: $message"; exit 2 }
proc require_command {name} {
  if {[llength [info commands $name]] == 0} { fatal "required command '$name' is unavailable" }
}
proc required_report {path command_words} {
  set command_name [lindex $command_words 0]
  require_command $command_name
  if {[catch {redirect -file $path {uplevel #0 $command_words}} message]} {
    fatal "report '$command_name' failed: $message"
  }
}
proc split_words {value} {
  if {$value eq ""} { return {} }
  return [regexp -all -inline {\S+} $value]
}

set top        [env_or DC_TOP ""]
set filelist   [env_or DC_FILELIST ""]
set sdc        [env_or DC_SDC ""]
set setup_tcl  [env_or DC_SETUP_TCL ""]
set work_dir   [env_or DC_WORK_DIR "work"]
set report_dir [env_or DC_REPORT_DIR "reports"]
set output_dir [env_or DC_OUTPUT_DIR "outputs"]
set netlist    [env_or DC_NETLIST "$output_dir/${top}_netlist.v"]
set ddc        [env_or DC_DDC "$output_dir/${top}.ddc"]
set sdf        [env_or DC_SDF "$output_dir/${top}.sdf"]
set sdc_out    [env_or DC_SDC_OUT "$output_dir/${top}.sdc"]
set target_lib [env_or DC_TARGET_LIBRARY ""]
set link_lib   [env_or DC_LINK_LIBRARY ""]

if {$top ne "upf_dc_demo"} { fatal "expected top upf_dc_demo, got '$top'" }
foreach path [list $filelist $sdc $setup_tcl] {
  if {$path eq "" || ![file exists $path]} { fatal "missing required input: $path" }
}
set syn_dir [file dirname $sdc]
set upf_file [file join $syn_dir upf upf_dc_demo.upf]
set upf_out [file join $syn_dir upf upf_dc_demo_synth.upf]
set loaded_upf [file join $report_dir loaded_upf.pre_compile.upf]
set timing_out [file join $syn_dir timing.rpt]
set timing_summary_out [file join $syn_dir timing_summary.rpt]
if {![file exists $upf_file]} { fatal "missing strict generated UPF: $upf_file" }

file mkdir $work_dir
file mkdir $report_dir
file mkdir $output_dir
# Every accepted report/output must come from this invocation.  Remove only
# transient products owned by this module before starting the registered run.
foreach stale [glob -nocomplain -directory $report_dir *] {
  file delete -force $stale
}
foreach stale [list $ddc $netlist $sdf $sdc_out $upf_out $timing_out $timing_summary_out] {
  if {[file exists $stale]} { file delete -force $stale }
}
set alib_dir [file join $work_dir alib]
file mkdir $alib_dir
define_design_lib WORK -path $work_dir
set_app_var alib_library_analysis_path $alib_dir
set_app_var hdlin_enable_upf_compatible_naming true
set_app_var verilogout_no_tri true
source $setup_tcl
if {$target_lib ne ""} { set_app_var target_library [split_words $target_lib] }
if {$link_lib ne ""} { set_app_var link_library [split_words $link_lib] }

# Read only the synthesizable digital RTL.  The same macro names have
# behavioral Verilog views for lint/compile, but their DC views must resolve
# from the PG-aware Liberty DB rather than become HDL designs.
set logic_filelist [file join $work_dir logic_rtl.f]
set source_fd [open $filelist r]
set logic_fd [open $logic_filelist w]
foreach line [split [read $source_fd] "\n"] {
  if {![regexp {upf_dc_demo_(pll_macro|sram_16x8|pad_in|pad_out)\.v$} $line]} {
    puts $logic_fd $line
  }
}
close $source_fd
close $logic_fd
analyze -format sverilog -vcs "-f $logic_filelist"
elaborate $top
current_design $top
link
uniquify

set macro_cell_names {
  upf_dc_demo_pll_macro
  upf_dc_demo_sram_16x8
  upf_dc_demo_pad_in
  upf_dc_demo_pad_out
}
set macro_instance_names {u_pll_macro u_sram_macro u_pad_in u_pad_out}
set macro_audit [open [file join $report_dir macro_blackbox_audit.rpt] w]
foreach cell_name $macro_cell_names {
  set objects [get_lib_cells -quiet */$cell_name]
  if {[sizeof_collection $objects] != 1} { fatal "missing PG-aware macro lib cell '$cell_name'" }
  puts $macro_audit "LIB_CELL=$cell_name PG_STUB=true"
}
foreach instance_name $macro_instance_names {
  set objects [get_cells -quiet $instance_name]
  if {[sizeof_collection $objects] != 1} { fatal "missing macro instance '$instance_name'" }
  set_dont_touch $objects
  set_ungroup $objects false
  puts $macro_audit "INSTANCE=$instance_name DONT_TOUCH=true"
}
close $macro_audit
set sw_core [get_cells -quiet u_sw_core]
if {[sizeof_collection $sw_core] != 1} { fatal "missing u_sw_core" }
set_ungroup $sw_core false

# Prove the source RTL is signal-only before UPF creates supply objects.
set reconcile [open [file join $report_dir pg_reconciliation.rpt] w]
foreach supply_name {VDD_AO VDD_PLL VDD_MEM VDDIO VDD_SW_IN VSS} {
  if {[sizeof_collection [get_ports -quiet $supply_name]] != 0} {
    fatal "functional RTL unexpectedly exposes PG port '$supply_name'"
  }
  puts $reconcile "RTL_PG_ABSENT port=$supply_name"
}
set macro_pg_map {
  u_pll_macro/VDD VDD_PLL
  u_pll_macro/VSS VSS
  u_sram_macro/VDD VDD_MEM
  u_sram_macro/VSS VSS
  u_pad_in/VDDIO VDDIO
  u_pad_in/VSSIO VSS
  u_pad_out/VDDIO VDDIO
  u_pad_out/VSSIO VSS
}
set macro_pg_paths {}
foreach {pin_path expected_net} $macro_pg_map {
  lappend macro_pg_paths $pin_path
  lassign [split $pin_path /] instance_name pin_name
  set macro_instance [get_cells -quiet $instance_name]
  if {[sizeof_collection $macro_instance] != 1} {
    fatal "missing macro instance for PG path '$pin_path'"
  }
  set ref_name [get_attribute $macro_instance ref_name]
  if {[lsearch -exact $macro_cell_names $ref_name] < 0} {
    fatal "PG path '$pin_path' resolves to unexpected ref '$ref_name'"
  }
  puts $reconcile "LIBERTY_PG pin=$pin_path ref=$ref_name pg_pin=$pin_name expected_net=$expected_net"
}
close $reconcile

require_command load_upf
set load_status [catch {
  redirect -tee -variable load_transcript {load_upf $upf_file}
} load_message]
if {$load_status} { fatal "load_upf failed: $load_message" }
set load_fd [open [file join $report_dir load_upf_transcript.rpt] w]
puts $load_fd $load_transcript
close $load_fd
if {[regexp -nocase {(^|\n)Error:|UPF-048|UPF_DC_DEMO_FATAL} $load_transcript]} {
  fatal "load_upf transcript contains an error diagnostic"
}
save_upf -full_upf $loaded_upf
if {![file exists $loaded_upf] || [file size $loaded_upf] == 0} {
  fatal "loaded canonical UPF did not produce an auditable saved view"
}

require_command get_power_domains
set domains [get_power_domains -quiet *]
set domain_names [lsort [get_object_name $domains]]
if {[llength $domain_names] != 2 || [lsearch -exact $domain_names PD_AO] < 0 ||
    [lsearch -exact $domain_names PD_SW] < 0} {
  fatal "expected exactly PD_AO and PD_SW, got '$domain_names'"
}

set_operating_conditions tt_025C_1v80
set_voltage -object_list {VDD_AO VDD_PLL VDD_MEM} 1.8
set_voltage -object_list {VDDIO} 3.3
set_voltage -object_list {VDD_SW_IN VDD_SW} 1.2
set_voltage -object_list {VSS} 0.0
read_sdc $sdc
set_fix_multiple_port_nets -all -buffer_constants

required_report [file join $report_dir check_design.pre_compile.rpt] {check_design}
required_report [file join $report_dir mv_check.pre_compile.rpt] {check_mv_design -verbose}
required_report [file join $report_dir power_domains.pre_compile.rpt] {report_power_domain}
required_report [file join $report_dir supply_connectivity.pre_compile.rpt] {report_supply_net}
set domain_fd [open [file join $report_dir power_domains.pre_compile.rpt] r]
set domain_text [read $domain_fd]
close $domain_fd
foreach token {SS_VDD_PLL_VSS SS_VDD_MEM_VSS SS_VDDIO_VSS} {
  if {[string first $token $domain_text] < 0} {
    fatal "PD_AO report is missing additional supply '$token'"
  }
}
set connectivity_fd [open $loaded_upf r]
set connectivity_text [read $connectivity_fd]
close $connectivity_fd
foreach pin_path $macro_pg_paths {
  if {[string first $pin_path $connectivity_text] < 0} {
    fatal "supply report does not resolve hierarchical PG path '$pin_path'"
  }
}

set compile_status [catch {
  redirect -tee -variable compile_transcript {compile_ultra -no_autoungroup}
} compile_message]
if {$compile_status} { fatal "compile_ultra failed: $compile_message" }
set compile_fd [open [file join $report_dir compile_transcript.rpt] w]
puts $compile_fd $compile_transcript
close $compile_fd
if {[regexp -nocase {(^|\n)Error:} $compile_transcript]} {
  fatal "compile_ultra transcript contains an error diagnostic"
}
link

# Expected macro blackboxes are permitted. No other unmapped/GTECH/SEQGEN leaf
# is accepted in the digital mapped design.
set unmapped [get_cells -hierarchical -quiet -filter "is_hierarchical == false && is_unmapped == true"]
foreach_in_collection cell $unmapped {
  set ref [get_attribute $cell ref_name]
  if {[lsearch -exact $macro_cell_names $ref] < 0} {
    fatal "unexpected unmapped leaf [get_object_name $cell] ref=$ref"
  }
}
set bad_generic [get_cells -hierarchical -quiet -filter "ref_name =~ GTECH* || ref_name =~ SEQGEN*"]
if {[sizeof_collection $bad_generic] != 0} {
  fatal "mapped digital design contains GTECH/SEQGEN cells"
}

set els_cells [get_cells -hierarchical -quiet -filter "ref_name =~ upf_dc_demo_els_*"]
set iso_cells $els_cells
set ls_cells [get_cells -hierarchical -quiet -filter "ref_name =~ upf_dc_demo_ls_*"]
set ls_cells [add_to_collection $ls_cells $els_cells]
set lp_audit [open [file join $report_dir inserted_low_power_cells.rpt] w]
puts $lp_audit "INSERTED_ISOLATION_COUNT=[sizeof_collection $iso_cells]"
puts $lp_audit "INSERTED_LEVEL_SHIFTER_COUNT=[sizeof_collection $ls_cells]"
foreach_in_collection cell $iso_cells {
  puts $lp_audit "ISO_CELL=[get_object_name $cell] REF=[get_attribute $cell ref_name]"
}
foreach_in_collection cell $ls_cells {
  puts $lp_audit "LS_CELL=[get_object_name $cell] REF=[get_attribute $cell ref_name]"
}
close $lp_audit
if {[sizeof_collection $iso_cells] != 9} { fatal "expected 9 mapped PD_SW isolation cells" }
if {[sizeof_collection $ls_cells] != 20} { fatal "expected 20 mapped AO/SW level shifters" }

required_report [file join $report_dir mv_check.rpt] {check_mv_design -verbose}
set mv_fd [open [file join $report_dir mv_check.rpt] r]
set mv_text [read $mv_fd]
close $mv_fd
foreach pattern {
  {Found [1-9][0-9]* pin to pin connections requiring level shifter}
  {Found [1-9][0-9]* net\(s\) without isolation}
  {UPF-048}
  {MV-046}
  {\(MV-229\)}
  {UPF-814}
  {doesn't match -applies_to_boundary filter}
} {
  if {[regexp -nocase $pattern $mv_text]} { fatal "unresolved MV diagnostic: $pattern" }
}

required_report [file join $report_dir power_domains.rpt] {report_power_domain}
required_report [file join $report_dir supply_nets.rpt] {report_supply_net}
required_report [file join $report_dir isolation.rpt] {report_isolation_cell}
required_report [file join $report_dir level_shifters.rpt] {report_level_shifter}
required_report [file join $report_dir qor.rpt] {report_qor}
required_report [file join $report_dir area.rpt] {report_area -hierarchy}
required_report $timing_summary_out {report_qor}
required_report $timing_out {report_timing -max_paths 20 -transition_time -nets -attributes}
required_report [file join $report_dir constraints.rpt] {report_constraint -all_violators}

change_names -rules verilog -hierarchy
write_file -format ddc -hierarchy -output $ddc
write_file -format verilog -hierarchy -pg -output $netlist
write_sdc $sdc_out
write_sdf $sdf
save_upf -full_upf $upf_out
foreach path [list $ddc $netlist $sdc_out $upf_out $timing_out $timing_summary_out] {
  if {![file exists $path] || [file size $path] == 0} { fatal "missing output: $path" }
}
set netlist_fd [open $netlist r]
set netlist_text [read $netlist_fd]
close $netlist_fd
# The abstract UPF power switch is preserved in the saved UPF rather than
# emitted as a physical switch instance by this teaching flow.  Therefore its
# input supply VDD_SW_IN need not survive as a Verilog port; require the
# switched rail and every supply that feeds emitted cells/macros here, while
# the saved-UPF audit below covers VDD_SW_IN and PSW_SW.
foreach pg_token {VDD_AO VDD_PLL VDD_MEM VDDIO VDD_SW VSS} {
  if {[string first $pg_token $netlist_text] < 0} {
    fatal "PG netlist is missing synthesized supply '$pg_token'"
  }
}
set saved_upf_fd [open $upf_out r]
set saved_upf_text [read $saved_upf_fd]
close $saved_upf_fd
foreach upf_token {VDD_SW_IN VDD_SW PSW_SW} {
  if {[string first $upf_token $saved_upf_text] < 0} {
    fatal "saved UPF is missing power-switch token '$upf_token'"
  }
}
foreach pin_path $macro_pg_paths {
  if {[string first $pin_path $saved_upf_text] < 0} {
    fatal "saved UPF is missing macro PG path '$pin_path'"
  }
}
puts "DC netlist: $netlist"
puts "DC written UPF: $upf_out"
puts "DC timing: $timing_out"
exit 0
