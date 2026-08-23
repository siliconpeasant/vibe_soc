# VC Static CDC flow.
# Reference: $VC_STATIC_HOME/doc/vcst/examples/CDC/logic_sync/vcst.tcl

set common [file join [file dirname [info script]] ../vc_static/vc_flow_common.tcl]
source $common

set filelist    [vc_require_env VC_FILELIST]
set top         [vc_require_env VC_TOP]
set sdc_in      [vc_env_or VC_SDC ""]
set summary     [vc_env_or VC_CDC_SUMMARY "report_cdc.summary.log"]
set detailed    [vc_env_or VC_CDC_REPORT "report_cdc.detailed.log"]
set gate_file   [vc_env_or VC_CDC_GATE "result_gate.txt"]
set max_blocking [vc_env_or VC_CDC_MAX_BLOCKING "0"]

# Official CDC examples start with enable_cdc.
set_app_var enable_cdc true

vc_read_design $filelist $top sverilog

set sdc [vc_prepare_constraints $sdc_in "vc_cdc.sdc" "cdc"]
read_sdc $sdc

check_cdc

report_violations -app CDC -gen_empty -file $summary
report_violations -app CDC -gen_empty -verbose -limit 0 -file $detailed
set blocking_ids [report_violations -app CDC -no_summary -limit 0   -severity {error warning} -id_list]
vc_finalize_result "cdc" $gate_file $max_blocking   [list $summary $detailed] $blocking_ids
puts "VC_STATIC CDC complete: $detailed"
quit
