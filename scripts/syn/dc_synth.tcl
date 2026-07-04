# Generic Design Compiler synthesis flow for vibe_soc modules.
# Configure through environment variables exported by scripts/common.mk.

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
set search_path_in [env_or DC_SEARCH_PATH ""]
set target_lib     [env_or DC_TARGET_LIBRARY ""]
set link_lib       [env_or DC_LINK_LIBRARY ""]
set symbol_lib     [env_or DC_SYMBOL_LIBRARY ""]
set compile_ultra  [env_or DC_COMPILE_ULTRA "1"]
set clock_gating   [env_or DC_CLOCK_GATING "0"]
set max_cores      [env_or DC_MAX_CORES "1"]

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

analyze -format sverilog -vcs "-f $filelist"
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

if {[bool_enabled $compile_ultra]} {
  if {[bool_enabled $clock_gating]} {
    compile_ultra -gate_clock
  } else {
    compile_ultra
  }
} else {
  compile
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

puts "DC netlist: $netlist"
puts "DC ddc:     $ddc"
puts "DC sdc:     $sdc_out"
puts "DC sdf:     $sdf"
exit 0
