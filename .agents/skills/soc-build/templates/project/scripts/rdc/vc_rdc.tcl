# VC Static RDC (native) flow.
# Reference: $VC_STATIC_HOME/doc/vcst/examples/RDC/NATIVE_RDC/test1.tcl
#            $VC_STATIC_HOME/doc/vcst/examples/RDC/SAM/run_top.tcl

set common [file join [file dirname [info script]] ../vc_static/vc_flow_common.tcl]
source $common

set filelist [vc_require_env VC_FILELIST]
set top      [vc_require_env VC_TOP]
set sdc_in   [vc_env_or VC_SDC ""]
set report   [vc_env_or VC_RDC_REPORT "report_rdc.log"]
set gate_file [vc_env_or VC_RDC_GATE "result_gate.txt"]
set max_blocking [vc_env_or VC_RDC_MAX_BLOCKING "0"]

# Official RDC examples start with enable_rdc.
set_app_var enable_rdc true
configure_console_messages -show both -tags [get_tags -app DESIGN]

vc_read_design $filelist $top sverilog

set sdc [vc_prepare_constraints $sdc_in "vc_rdc.sdc" "rdc"]
read_sdc $sdc

check_rdc

# report_rdc is the native reporter (NATIVE_RDC examples).
report_rdc -file $report
report_rdc
set blocking_ids [report_rdc -no_summary -limit 0   -severity {error warning} -id_list]
vc_finalize_result "rdc" $gate_file $max_blocking [list $report] $blocking_ids
puts "VC_STATIC RDC complete: $report"
quit
