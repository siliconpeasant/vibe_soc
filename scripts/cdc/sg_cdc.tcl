proc require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    error "Required environment variable $name is not set"
  }
  return $::env($name)
}

proc read_hdl_filelist {filelist project_root} {
  set fp [open $filelist r]
  while {[gets $fp raw] >= 0} {
    set line [string trim $raw]
    if {$line eq ""} { continue }
    if {[string match "#*" $line]} { continue }
    if {[string match "//*" $line]} { continue }
    if {[string match "+incdir+*" $line]} { continue }
    if {[string match "+define+*" $line]} { continue }
    if {[string match "-y *" $line]} { continue }
    set path [string map [list {$SOC} $project_root] $line]
    read_file -type hdl $path
  }
  close $fp
}

proc prepare_sgdc {top} {
  if {[info exists ::env(SG_SGDC)] && $::env(SG_SGDC) ne ""} {
    if {![file exists $::env(SG_SGDC)]} {
      error "SGDC file not found: $::env(SG_SGDC)"
    }
    return $::env(SG_SGDC)
  }

  set clock_port "clk"
  if {[info exists ::env(SG_CLOCK_PORT)]} { set clock_port $::env(SG_CLOCK_PORT) }
  set reset_port "rst_n"
  if {[info exists ::env(SG_RESET_PORT)]} { set reset_port $::env(SG_RESET_PORT) }
  set reset_value "0"
  if {[info exists ::env(SG_RESET_VALUE)]} { set reset_value $::env(SG_RESET_VALUE) }
  set sgdc_path "cdc.sgdc"
  set fp [open $sgdc_path w]
  puts $fp "current_design $top"
  if {$clock_port ne ""} { puts $fp "clock -name $clock_port" }
  if {$reset_port ne ""} { puts $fp "reset -name $reset_port -value $reset_value" }
  close $fp
  return $sgdc_path
}

set project_root [require_env PROJECT_ROOT]
set spyglass_home [require_env SPYGLASS_HOME]
set filelist [require_env SG_FILELIST]
set top [require_env SG_TOP]
set goal [require_env SG_GOAL]
set methodology [require_env SG_METHODOLOGY]
set project_name "${top}_cdc"
if {[info exists ::env(SG_PROJECT_NAME)] && $::env(SG_PROJECT_NAME) ne ""} {
  set project_name $::env(SG_PROJECT_NAME)
}
set sgdc_path [prepare_sgdc $top]

new_project $project_name -force
set_option language_mode verilog
set_option enable_save_restore no
set_option top $top
current_methodology $methodology
current_goal $goal -alltop
read_file -type sgdc $sgdc_path
read_hdl_filelist $filelist $project_root
run_goal
write_report moresimple > moresimple.rpt
write_report waiver > waiver.rpt
quit
