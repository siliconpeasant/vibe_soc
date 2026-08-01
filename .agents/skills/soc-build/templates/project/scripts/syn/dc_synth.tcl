# Generic Design Compiler synthesis flow for vibe_soc modules.
# Configure through environment variables exported by scripts/common.mk.

set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir .. tcl flow_common.tcl]
flow::set_fatal_prefix "DC_FATAL"

proc env_or {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} {
    return $::env($name)
  }
  return $default_value
}

proc split_words {value} {
  if {$value eq ""} {
    return {}
  }
  return [regexp -all -inline {\S+} $value]
}

proc bool_enabled {value} {
  return [expr {[string match -nocase "1" $value] ||
                [string match -nocase "true" $value] ||
                [string match -nocase "yes" $value]}]
}

set top            [env_or DC_TOP ""]
set filelist       [env_or DC_FILELIST ""]
set sdc            [env_or DC_SDC ""]
set setup_tcl      [env_or DC_SETUP_TCL ""]
set work_dir       [env_or DC_WORK_DIR "work"]
set report_dir     [env_or DC_REPORT_DIR "reports"]
set output_dir     [env_or DC_OUTPUT_DIR "outputs"]
set netlist        [env_or DC_NETLIST "$output_dir/${top}_netlist.v"]
set ddc            [env_or DC_DDC "$output_dir/${top}.ddc"]
set sdf            [env_or DC_SDF "$output_dir/${top}.sdf"]
set sdc_out        [env_or DC_SDC_OUT "$output_dir/${top}.sdc"]
set svf            [env_or DC_SVF "$output_dir/${top}.svf"]
set search_path_in [env_or DC_SEARCH_PATH ""]
set target_lib     [env_or DC_TARGET_LIBRARY ""]
set link_lib       [env_or DC_LINK_LIBRARY ""]
set symbol_lib     [env_or DC_SYMBOL_LIBRARY ""]
set compile_ultra  [env_or DC_COMPILE_ULTRA "1"]
set compile_options [env_or DC_COMPILE_OPTIONS ""]
set clock_gating   [env_or DC_CLOCK_GATING "0"]
set max_cores      [env_or DC_MAX_CORES "1"]
set rtl_define     [env_or DC_RTL_DEFINE "SYNTHESIS"]

if {$top eq ""} {
  puts stderr "DC_TOP is required"
  exit 2
}
if {$filelist eq "" || ![file exists $filelist]} {
  puts stderr "DC_FILELIST is missing or does not exist: $filelist"
  exit 2
}

file mkdir $work_dir
file mkdir $report_dir
file mkdir $output_dir
foreach stale [list $netlist $ddc $sdf $sdc_out $svf] {
  if {[file exists $stale]} {
    file delete -force $stale
  }
}

if {[llength [info commands set_svf]] == 0} {
  puts stderr "set_svf is unavailable; Formality guidance cannot be recorded"
  exit 2
}
if {[catch {set_svf $svf} svf_message]} {
  puts stderr "unable to enable Formality guidance output '$svf': $svf_message"
  exit 2
}

define_design_lib WORK -path $work_dir

if {$max_cores ne ""} {
  set_host_options -max_cores $max_cores
}

set_app_var search_path [concat [get_app_var search_path] [split_words $search_path_in]]

if {$setup_tcl ne ""} {
  if {![file exists $setup_tcl]} {
    puts stderr "DC_SETUP_TCL does not exist: $setup_tcl"
    exit 2
  }
  source $setup_tcl
}

if {$target_lib ne ""} {
  set_app_var target_library [split_words $target_lib]
}
set link_words [split_words $link_lib]
if {[llength $link_words] > 0} {
  set_app_var link_library $link_words
} elseif {[llength [get_app_var target_library]] > 0} {
  set_app_var link_library [concat [list *] [get_app_var target_library]]
}
if {$symbol_lib ne ""} {
  set_app_var symbol_library [split_words $symbol_lib]
}

set_app_var verilogout_no_tri true

puts "DC top:       $top"
puts "DC filelist:  $filelist"
puts "DC SDC:       $sdc"
puts "DC reports:   $report_dir"
puts "DC outputs:   $output_dir"
puts "DC targetlib: [get_app_var target_library]"
puts "DC linklib:   [get_app_var link_library]"

set analyze_options "-f $filelist"
if {$rtl_define ne ""} {
  set analyze_options "+define+$rtl_define $analyze_options"
}
analyze -format sverilog -vcs $analyze_options
elaborate $top
current_design $top
link
uniquify

redirect -file "$report_dir/check_design.pre_compile.rpt" {check_design}

if {$sdc ne ""} {
  if {![file exists $sdc]} {
    puts stderr "DC_SDC does not exist: $sdc"
    exit 2
  }
  read_sdc $sdc
}

set_fix_multiple_port_nets -all -buffer_constants

set compile_command [list [expr {[bool_enabled $compile_ultra] ? "compile_ultra" : "compile"}]]
if {[bool_enabled $clock_gating] && [bool_enabled $compile_ultra]} {
  lappend compile_command -gate_clock
}
foreach option [split_words $compile_options] {
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
redirect -file "$report_dir/check_design.rpt" {check_design}
redirect -file "$report_dir/qor.rpt" {report_qor}
redirect -file "$report_dir/timing.rpt" {report_timing -max_paths 20 -transition_time -nets -attributes}
redirect -file "$report_dir/area.rpt" {report_area -hierarchy}
redirect -file "$report_dir/power.rpt" {report_power -hierarchy}
redirect -file "$report_dir/resources.rpt" {report_resources -hierarchy}
redirect -file "$report_dir/constraints.rpt" {report_constraint -all_violators}

write -format ddc -hierarchy -output $ddc
write -format verilog -hierarchy -output $netlist
write_sdc $sdc_out
write_sdf $sdf

if {[catch {set_svf -off} svf_message]} {
  puts stderr "unable to close Formality guidance output '$svf': $svf_message"
  exit 2
}
if {![file exists $svf] || [file size $svf] == 0} {
  puts stderr "missing or empty Formality guidance output: $svf"
  exit 2
}
foreach path [list \
  $netlist $ddc $sdf $sdc_out $svf \
  [file join $report_dir check_design.pre_compile.rpt] \
  [file join $report_dir check_design.rpt] \
  [file join $report_dir qor.rpt] \
  [file join $report_dir timing.rpt] \
  [file join $report_dir area.rpt] \
  [file join $report_dir power.rpt] \
  [file join $report_dir resources.rpt] \
  [file join $report_dir constraints.rpt] \
  [file join $report_dir compile_transcript.rpt] \
] {
  flow::require_file $path
}

puts "DC netlist: $netlist"
puts "DC ddc:     $ddc"
puts "DC sdc:     $sdc_out"
puts "DC sdf:     $sdf"
puts "DC svf:     $svf"
puts "DC_OUTPUTS_READY top=$top netlist=$netlist svf=$svf"
exit 0
