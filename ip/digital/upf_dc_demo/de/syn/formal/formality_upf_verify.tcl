# Post-DC Formality check for RTL + canonical UPF versus netlist + saved UPF.

proc env_required {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    puts stderr "UPF_FORMAL_FATAL: required environment variable '$name' is unset"
    exit 2
  }
  return $::env($name)
}
proc fatal {message} { puts stderr "UPF_FORMAL_FATAL: $message"; exit 2 }
proc require_file {path} {
  if {![file exists $path] || [file size $path] == 0} {
    fatal "missing or empty input: $path"
  }
}
proc split_words {value} {
  if {$value eq ""} { return {} }
  return [regexp -all -inline {\S+} $value]
}
proc write_report {path command_words} {
  if {[catch {redirect -file $path {uplevel #0 $command_words}} message]} {
    fatal "report '[lindex $command_words 0]' failed: $message"
  }
  require_file $path
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

set top [env_required FM_TOP]
set project_root [env_required PROJECT_ROOT]
set filelist [env_required FM_RTL_FILELIST]
set netlist [env_required FM_NETLIST]
set reference_upf [env_required FM_REFERENCE_UPF]
set implementation_upf [env_required FM_IMPLEMENTATION_UPF]
set svf [env_required FM_SVF]
set library_dbs [split_words [env_required FM_LIB_DB]]
set run_dir [env_required FM_RUN_DIR]

if {$top ne "upf_dc_demo"} { fatal "expected top upf_dc_demo, got '$top'" }
foreach path [concat [list $filelist $netlist $reference_upf $implementation_upf $svf] $library_dbs] {
  require_file $path
}
file mkdir $run_dir
set rtl_files [logic_rtl_files $filelist $project_root]

# The Synopsys multivoltage flow requires all logic/low-power libraries and
# the DC-produced SVF to be loaded before either design container.
set synopsys_auto_setup true
set hdlin_library_autocorrect true
set verification_force_upf_supplies_on false
if {[catch {set_svf $svf} message]} { fatal "set_svf failed: $message" }
if {[catch {read_db $library_dbs} message]} { fatal "read_db failed: $message" }

if {[catch {read_verilog -r $rtl_files} message]} {
  fatal "reference RTL read failed: $message"
}
if {[catch {set_top r:/WORK/$top} message]} { fatal "reference set_top failed: $message" }
if {[catch {load_upf -r $reference_upf} message]} {
  fatal "reference load_upf failed: $message"
}

if {[catch {read_verilog -i $netlist} message]} {
  fatal "implementation netlist read failed: $message"
}
if {[catch {set_top i:/WORK/$top} message]} { fatal "implementation set_top failed: $message" }
if {[catch {load_upf -i $implementation_upf} message]} {
  fatal "implementation load_upf failed: $message"
}

write_report [file join $run_dir library_defects.rpt] {report_libraries -defects errors}
write_report [file join $run_dir upf_reference.rpt] {report_upf -r -verbose}
write_report [file join $run_dir upf_implementation.rpt] {report_upf -i -verbose}
write_report [file join $run_dir setup_status.rpt] {report_setup_status -all}

set match_result 0
if {[catch {redirect -file [file join $run_dir match_status.rpt] {
  set match_result [match]
  report_unmatched_points
}} message]} {
  fatal "match failed to run: $message"
}
require_file [file join $run_dir match_status.rpt]
if {!$match_result} { fatal "Formality match returned failure" }

set verify_result 0
if {[catch {set verify_result [verify]} message]} {
  fatal "verify failed to run: $message"
}
write_report [file join $run_dir verification_status.rpt] {report_status -last -short}
set verification_fd [open [file join $run_dir verification_status.rpt] a]
puts $verification_fd "VERIFICATION_STATUS=$verification_status"
close $verification_fd
if {!$verify_result || $verification_status ne "SUCCEEDED"} {
  fatal "verification did not succeed: result=$verify_result status=$verification_status"
}

puts "UPF_FORMAL_PASS top=$top status=$verification_status"
exit 0
