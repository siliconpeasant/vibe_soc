# VC Static lint flow.
# Reference: $VC_STATIC_HOME/doc/vcst/examples/LINT/lint_rtl_goal/vc_lint.tcl

set common [file join [file dirname [info script]] ../vc_static/vc_flow_common.tcl]
source $common

set project_root [vc_require_env PROJECT_ROOT]
set vc_home      [vc_require_env VC_STATIC_HOME]
set filelist     [vc_require_env VC_FILELIST]
set top          [vc_require_env VC_TOP]
set goal         [vc_env_or VC_LINT_GOAL "lint_rtl"]
set guideware    [vc_env_or VC_LINT_GUIDEWARE \
  "$vc_home/auxx/monet/tcl/GuideWare/block/rtl_handoff/lint/"]
set report_file  [vc_env_or VC_LINT_REPORT "report_lint.txt"]
set summary_file [vc_env_or VC_LINT_SUMMARY "report_lint.summary.txt"]
set gate_file    [vc_env_or VC_LINT_GATE "result_gate.txt"]
set max_blocking [vc_env_or VC_LINT_MAX_BLOCKING "0"]

set search_path "."
set link_library " "

# App var to enable Lint Analysis (official lint_rtl_goal example).
set_app_var enable_lint true

# Goal Configuration — recommended lint_rtl guideware.
configure_lint_methodology -path $guideware -goal $goal
configure_lint_setup -goal $goal

vc_read_design $filelist $top sverilog

# Run Lint Checks
check_lint

# Third-party / foundry models may be waived after check_lint (waive exists).
# In-house RTL must be fixed. Policy: 2026-08-14.
set tp_waiver [file join $project_root scripts/lint/waivers_third_party.tcl]
if {[file exists $tp_waiver]} {
  source $tp_waiver
}

# Analysis Reports
report_violations -app {lint} -gen_empty -file $summary_file
report_violations -app {lint} -gen_empty -verbose -limit 0 -file $report_file
set blocking_ids [report_violations -app {lint} -no_summary -limit 0   -severity {error warning} -id_list]
vc_finalize_result "lint" $gate_file $max_blocking   [list $summary_file $report_file] $blocking_ids
puts "VC_STATIC lint complete: $report_file"
quit
