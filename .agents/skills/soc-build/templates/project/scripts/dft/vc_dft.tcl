# VC SpyGlass DFT (TestMAX Advisor) — VCUM flow.
# Reference:
#   $VC_STATIC_HOME/doc/vcst/VC_SpyGlass_Docs/.../vcsg_testmax_ug/getting_started/vcum_flow_0.html
#   configure_dft_setup -goal dft_scan_ready ; check_dft

set common [file join [file dirname [info script]] ../vc_static/vc_flow_common.tcl]
source $common

set filelist [vc_require_env VC_FILELIST]
set top      [vc_require_env VC_TOP]
set goal     [vc_env_or VC_DFT_GOAL "dft_scan_ready"]
# Classic SpyGlass used "dft/dft_scan_ready"; VCUM uses "dft_scan_ready".
regsub {^dft/} $goal {} goal
set best_practice [vc_env_or VC_DFT_BEST_PRACTICE "0"]
set report_file   [vc_env_or VC_DFT_REPORT "report_dft.txt"]
set summary_file  [vc_env_or VC_DFT_SUMMARY "report_dft.summary.txt"]
set gate_file     [vc_env_or VC_DFT_GATE "result_gate.txt"]
set max_blocking  [vc_env_or VC_DFT_MAX_BLOCKING "0"]
set setup_hook    [vc_env_or VC_DFT_SETUP_TCL ""]
set search_path_extra [vc_env_or VC_DFT_SEARCH_PATH ""]
set link_library_extra [vc_env_or VC_DFT_LINK_LIBRARY ""]

# VCUM: enable DFT before design read.
set_app_var enable_dft true

if {$search_path_extra ne ""} {
  set search_path $search_path_extra
}
if {$link_library_extra ne ""} {
  set link_library $link_library_extra
}

vc_read_design $filelist $top sverilog

# Optional reviewed module hook (VC Static Tcl), e.g. de/dft/*_lib.tcl.
if {$setup_hook ne ""} {
  if {![file exists $setup_hook]} {
    error "VC_DFT_SETUP_TCL not found: $setup_hook"
  }
  puts "VC_STATIC DFT: sourcing setup $setup_hook"
  source $setup_hook
} else {
  # Bootstrap minimal test constraints from env (mirrors former SGDC bootstrap).
  set clock_port [vc_env_or VC_CLOCK_PORT "clk"]
  set reset_port [vc_env_or VC_RESET_PORT "rst_n"]
  set reset_value [vc_env_or VC_RESET_VALUE "0"]
  set test_mode_port [vc_env_or VC_TEST_MODE_PORT ""]
  set test_mode_value [vc_env_or VC_TEST_MODE_VALUE "1"]
  set test_rst_port [vc_env_or VC_TEST_RST_PORT ""]

  if {$clock_port ne ""} {
    # create_test_clock is the TestMAX API for DFT clocks.
    if {[catch {create_test_clock $clock_port -scanshift -capture} msg]} {
      puts "VC_STATIC DFT: create_test_clock fallback ($msg); using create_clock"
      create_clock -name $clock_port -period [vc_env_or VC_CLOCK_PERIOD "10"] [list $clock_port]
    }
  }
  if {$test_mode_port ne ""} {
    set_test_mode -name $test_mode_port -value $test_mode_value
  }
  if {$reset_port ne ""} {
    if {$reset_value eq "1"} {
      set sense "high"
    } else {
      set sense "low"
    }
    if {[catch {create_reset -name $reset_port -sense $sense [list $reset_port]} msg]} {
      puts "VC_STATIC DFT: create_reset skipped ($msg)"
    }
  }
  if {$test_rst_port ne ""} {
    if {[catch {create_reset -name $test_rst_port -sense low [list $test_rst_port]} msg]} {
      puts "VC_STATIC DFT: test_rst create_reset skipped ($msg)"
    }
  }
}

puts "VC_STATIC DFT: configure_dft_setup -goal $goal"
configure_dft_setup -goal $goal
check_dft

if {$best_practice eq "1" || [string match -nocase "true" $best_practice] || \
    [string match -nocase "yes" $best_practice]} {
  puts "VC_STATIC DFT: configure_dft_setup -goal dft_best_practice"
  configure_dft_setup -goal dft_best_practice
  check_dft
}

report_violations -app {DFT} -gen_empty -file $summary_file
report_violations -app {DFT} -gen_empty -verbose -limit 0   -report {sg_moresimple} -file $report_file
set blocking_ids [report_violations -app {DFT} -no_summary -limit 0   -severity {error warning} -id_list]
vc_finalize_result "dft" $gate_file $max_blocking   [list $summary_file $report_file] $blocking_ids
puts "VC_STATIC DFT complete: $report_file"
quit
