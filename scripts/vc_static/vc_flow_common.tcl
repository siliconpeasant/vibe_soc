# Shared helpers for VC Static lint/CDC/RDC/DFT flows.
# Pattern follows official examples under:
#   $VC_STATIC_HOME/doc/vcst/examples/{LINT,CDC,RDC}

proc vc_require_env {name} {
  if {![info exists ::env($name)] || $::env($name) eq ""} {
    error "Required environment variable $name is not set"
  }
  return $::env($name)
}

proc vc_env_or {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} {
    return $::env($name)
  }
  return $default_value
}

proc vc_expand_path {path project_root} {
  return [string map [list {$SOC} $project_root {$PROJECT_ROOT} $project_root] $path]
}

# Materialize a VCS-style filelist for analyze -f, expanding $SOC placeholders.
proc vc_prepare_filelist {src_filelist project_root out_filelist} {
  if {![file exists $src_filelist]} {
    error "Filelist not found: $src_filelist"
  }
  set ifp [open $src_filelist r]
  set ofp [open $out_filelist w]
  set count 0
  while {[gets $ifp raw] >= 0} {
    set line [string trim $raw]
    if {$line eq ""} { continue }
    if {[string match "#*" $line]} { continue }
    if {[string match "//*" $line]} { continue }
    set line [vc_expand_path $line $project_root]
    puts $ofp $line
    incr count
  }
  close $ifp
  close $ofp
  if {$count == 0} {
    error "Filelist has no usable entries: $src_filelist"
  }
  return $out_filelist
}

# analyze + elaborate from project filelist.
# VC Static treats native -f as -format (CMD-010 if used as a filelist flag).
# Official lint_rtl_goal / DC style passes the filelist through -vcs.
proc vc_read_design {filelist top {format sverilog}} {
  set project_root [vc_require_env PROJECT_ROOT]
  set prepared "vc_static.f"
  vc_prepare_filelist $filelist $project_root $prepared

  set vcs_opts [vc_env_or VC_ANALYZE_VCS_OPTS \
    "-sverilog +libext+.v+.sv+.svh+.vp+.svp"]
  set analyze_vcs "-f $prepared $vcs_opts"

  puts "VC_STATIC: analyze -format $format -vcs {$analyze_vcs}"
  if {[catch {analyze -format $format -vcs $analyze_vcs} analyze_err]} {
    error "VC_STATIC: analyze failed: $analyze_err"
  }
  puts "VC_STATIC: elaborate $top"
  if {[catch {elaborate $top} elab_err]} {
    error "VC_STATIC: elaborate failed: $elab_err"
  }
}

# Prefer module SDC when present; otherwise write a minimal clock/reset SDC.
proc vc_prepare_constraints {sdc_path out_sdc mode} {
  if {$sdc_path ne "" && [file exists $sdc_path]} {
    puts "VC_STATIC: using SDC $sdc_path"
    return $sdc_path
  }

  set clock_port [vc_env_or VC_CLOCK_PORT "clk"]
  set reset_port [vc_env_or VC_RESET_PORT "rst_n"]
  set reset_value [vc_env_or VC_RESET_VALUE "0"]
  set clock_period [vc_env_or VC_CLOCK_PERIOD "10"]

  set fp [open $out_sdc w]
  puts $fp "# Auto-generated minimal SDC for VC Static $mode"
  if {$clock_port ne ""} {
    puts $fp "create_clock -name $clock_port -period $clock_period \{$clock_port\}"
    puts $fp "set_clock_groups -asynchronous -group \{$clock_port\}"
  }
  if {$reset_port ne "" && ($mode eq "rdc" || $mode eq "cdc")} {
    if {$reset_value eq "1"} {
      set sense "high"
    } else {
      set sense "low"
    }
    # create_reset is valid inside VC Static constraint files (see RDC/SAM/top.sdc).
    puts $fp "create_reset -name $reset_port -sense $sense \{$reset_port\}"
  }
  close $fp
  puts "VC_STATIC: generated constraints $out_sdc"
  return $out_sdc
}

# Finalize VC Static text reports and write a small machine-readable result
# gate. The caller obtains blocking IDs from the documented -id_list command
# result, so no human-report text parsing is required.
proc vc_finalize_result {flow gate_file max_blocking report_files blocking_ids} {
  if {![string is integer -strict $max_blocking] || $max_blocking < 0} {
    error "VC_STATIC $flow: max blocking violations must be a non-negative integer"
  }

  set marker "# VC_STATIC_REPORT_COMPLETE flow=$flow"
  foreach report_file $report_files {
    if {![file exists $report_file]} {
      error "VC_STATIC $flow: expected report was not generated: $report_file"
    }
    set fp [open $report_file a]
    puts $fp ""
    puts $fp $marker
    close $fp
    if {[file size $report_file] == 0} {
      error "VC_STATIC $flow: report is empty after finalization: $report_file"
    }
  }

  set blocking_count [llength $blocking_ids]
  if {$blocking_count <= $max_blocking} {
    set status "pass"
  } else {
    set status "fail"
  }

  file mkdir [file dirname $gate_file]
  set fp [open $gate_file w]
  puts $fp "format=vc-static-result-v1"
  puts $fp "flow=$flow"
  puts $fp "blocking_severities=error,warning"
  puts $fp "blocking_count=$blocking_count"
  puts $fp "max_blocking=$max_blocking"
  puts $fp "status=$status"
  puts $fp "# VC_STATIC_RESULT_COMPLETE flow=$flow"
  close $fp

  puts "VC_STATIC_RESULT flow=$flow blocking=$blocking_count max=$max_blocking status=$status"
  if {$status ne "pass"} {
    error "VC_STATIC $flow: $blocking_count blocking error/warning violation(s) exceed maximum $max_blocking"
  }
}
