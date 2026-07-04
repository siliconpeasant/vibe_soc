proc require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    error "Required environment variable $name is not set"
  }
  return $::env($name)
}

proc read_hdl_filelist {filelist project_root} {
  set fp [open $filelist r]
  set lines [split [read $fp] "\n"]
  close $fp

  set incdirs {}
  set defines {}
  set hdl_files {}

  foreach raw $lines {
    set line [string trim $raw]
    if {$line eq ""} { continue }
    if {[string match "#*" $line]} { continue }
    if {[string match "//*" $line]} { continue }
    if {[string match "+incdir+*" $line]} {
      lappend incdirs [string map [list {$SOC} $project_root] [string range $line [string length "+incdir+"] end]]
      continue
    }
    if {[string match "+define+*" $line]} {
      lappend defines [string map [list {$SOC} $project_root] [string range $line [string length "+define+"] end]]
      continue
    }
    if {[string match "-y *" $line]} { continue }
    set path [string map [list {$SOC} $project_root] $line]
    set ext [string tolower [file extension $path]]
    if {$ext ni {.v .vh .sv .svh .vp .svp}} { continue }
    lappend hdl_files $path
  }

  if {[llength $incdirs] > 0} {
    set_option incdir $incdirs
  }
  if {[llength $defines] > 0} {
    set_option define $defines
  }
  foreach path $hdl_files {
    read_file -type hdl $path
  }
}

set project_root [require_env PROJECT_ROOT]
set spyglass_home [require_env SPYGLASS_HOME]
set filelist [require_env SG_FILELIST]
set top [require_env SG_TOP]
set goal [require_env SG_GOAL]
set methodology [require_env SG_METHODOLOGY]
set project_name "${top}_lint"
if {[info exists ::env(SG_PROJECT_NAME)] && $::env(SG_PROJECT_NAME) ne ""} {
  set project_name $::env(SG_PROJECT_NAME)
}

new_project $project_name -force
set_option language_mode verilog
set_option enableV05 yes
set_option enableSV yes
set_option enableSV09 yes
set_option enable_save_restore no
set_option top $top
current_methodology $methodology
current_goal $goal -alltop
read_hdl_filelist $filelist $project_root
run_goal
write_report moresimple > moresimple.rpt
write_report no_msg_reporting_rules > no_msg_reporting_rules.rpt
quit
