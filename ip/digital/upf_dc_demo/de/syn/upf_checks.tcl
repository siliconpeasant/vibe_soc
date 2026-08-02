# upf_dc_demo-specific assertions for the public DC+UPF synthesis engine.

proc dc_upf_post_elaborate {} {
  global top report_dir macro_cell_names macro_instance_names
  global core_instance_names controller_instance_names macro_pg_paths

  if {$top ne "upf_dc_demo"} {
    flow::fatal "expected top upf_dc_demo, got '$top'"
  }
  set macro_cell_names {
    upf_dc_demo_pll_macro
    upf_dc_demo_sram_16x8
    upf_dc_demo_pad_in
    upf_dc_demo_pad_out
  }
  set macro_instance_names {u_pll_macro u_sram_macro u_pad_in u_pad_out}
  set core_instance_names {u_sw_core u_acc_core u_peri_core u_media_core}
  set controller_instance_names {u_aon_ctrl u_acc_aon_ctrl u_peri_aon_ctrl u_media_aon_ctrl}

  set macro_audit [open [file join $report_dir macro_blackbox_audit.rpt] w]
  foreach cell_name $macro_cell_names {
    set objects [get_lib_cells -quiet */$cell_name]
    if {[sizeof_collection $objects] != 1} {
      flow::fatal "missing PG-aware macro lib cell '$cell_name'"
    }
    puts $macro_audit "LIB_CELL=$cell_name PG_STUB=true"
  }
  foreach instance_name $macro_instance_names {
    set objects [get_cells -quiet $instance_name]
    if {[sizeof_collection $objects] != 1} {
      flow::fatal "missing macro instance '$instance_name'"
    }
    set_dont_touch $objects
    set_ungroup $objects false
    puts $macro_audit "INSTANCE=$instance_name DONT_TOUCH=true"
  }
  close $macro_audit
  if {[sizeof_collection [get_cells -hierarchical -quiet *u_power_switch_macro*]] != 0} {
    flow::fatal "RTL/synthesis hierarchy contains forbidden power-switch macro instance"
  }
  foreach instance_name [concat $core_instance_names $controller_instance_names] {
    set objects [get_cells -quiet $instance_name]
    if {[sizeof_collection $objects] != 1} {
      flow::fatal "missing required instance '$instance_name'"
    }
    set_ungroup $objects false
  }

  set reconcile [open [file join $report_dir pg_reconciliation.rpt] w]
  foreach supply_name {
    VDD_AO VDD_PLL VDD_MEM VDDIO
    VDD_SW_IN VDD_SW VDD_ACC_IN VDD_ACC VDD_PERI_IN VDD_PERI
    VDD_MEDIA_IN VDD_MEDIA VSS
  } {
    if {[sizeof_collection [get_ports -quiet $supply_name]] != 0} {
      flow::fatal "functional RTL unexpectedly exposes PG port '$supply_name'"
    }
    puts $reconcile "RTL_PG_ABSENT port=$supply_name"
  }
  set macro_pg_map {
    u_pll_macro/VDD VDD_PLL
    u_pll_macro/VSS VSS
    u_sram_macro/VDD VDD_MEM
    u_sram_macro/VSS VSS
    u_pad_in/VDDIO VDDIO
    u_pad_in/VSSIO VSS
    u_pad_out/VDDIO VDDIO
    u_pad_out/VSSIO VSS
  }
  set macro_pg_paths {}
  foreach {pin_path expected_net} $macro_pg_map {
    lappend macro_pg_paths $pin_path
    lassign [split $pin_path /] instance_name pin_name
    set macro_instance [get_cells -quiet $instance_name]
    if {[sizeof_collection $macro_instance] != 1} {
      flow::fatal "missing macro instance for PG path '$pin_path'"
    }
    set ref_name [get_attribute $macro_instance ref_name]
    if {[lsearch -exact $macro_cell_names $ref_name] < 0} {
      flow::fatal "PG path '$pin_path' resolves to unexpected ref '$ref_name'"
    }
    puts $reconcile "LIBERTY_PG pin=$pin_path ref=$ref_name pg_pin=$pin_name expected_net=$expected_net"
  }
  close $reconcile
}

proc dc_upf_post_load_upf {} {
  set domains [get_power_domains -quiet *]
  set domain_names [lsort [get_object_name $domains]]
  set expected_domain_names [lsort {PD_AO PD_SW PD_ACC PD_PERI PD_MEDIA}]
  if {$domain_names ne $expected_domain_names} {
    flow::fatal "expected exactly five domains '$expected_domain_names', got '$domain_names'"
  }
  set_operating_conditions tt_025C_1v80
  set_voltage -object_list {VDD_AO VDD_PLL VDD_MEM} 1.8
  set_voltage -object_list {VDDIO} 3.3
  set_voltage -object_list {
    VDD_SW_IN VDD_SW VDD_ACC_IN VDD_ACC VDD_PERI_IN VDD_PERI
    VDD_MEDIA_IN VDD_MEDIA
  } 1.2
  set_voltage -object_list {VSS} 0.0
}

proc dc_upf_pre_compile {} {
  global report_dir loaded_upf macro_pg_paths

  set domain_fd [open [file join $report_dir power_domains.pre_compile.rpt] r]
  set domain_text [read $domain_fd]
  close $domain_fd
  foreach token {SS_VDD_PLL_VSS SS_VDD_MEM_VSS SS_VDDIO_VSS} {
    if {[string first $token $domain_text] < 0} {
      flow::fatal "PD_AO report is missing additional supply '$token'"
    }
  }
  foreach forbidden_handle {
    extra_supplies_4 extra_supplies_5 extra_supplies_6 extra_supplies_7
    extra_supplies_8 extra_supplies_9 extra_supplies_10 extra_supplies_11
    extra_supplies_12
  } {
    if {[string first $forbidden_handle $domain_text] >= 0} {
      flow::fatal "PD_AO report contains forbidden switch-rail handle '$forbidden_handle'"
    }
  }
  set connectivity_fd [open $loaded_upf r]
  set connectivity_text [read $connectivity_fd]
  close $connectivity_fd
  foreach pin_path $macro_pg_paths {
    if {[string first $pin_path $connectivity_text] < 0} {
      flow::fatal "saved loaded UPF does not resolve hierarchical PG path '$pin_path'"
    }
  }
  if {[regexp -all {create_power_switch[[:space:]]+PSW_} $connectivity_text] != 4} {
    flow::fatal "loaded UPF does not contain exactly four abstract switches"
  }
  if {[regexp -all {create_supply_set[[:space:]]+SS_} $connectivity_text] != 12} {
    flow::fatal "loaded UPF does not contain exactly twelve supply sets"
  }
  foreach token {
    PSW_SW PSW_ACC PSW_PERI PSW_MEDIA
    SS_VDD_AO_VSS SS_VDD_PLL_VSS SS_VDD_MEM_VSS SS_VDDIO_VSS
    SS_VDD_SW_IN_VSS SS_VDD_SW_VSS SS_VDD_ACC_IN_VSS SS_VDD_ACC_VSS
    SS_VDD_PERI_IN_VSS SS_VDD_PERI_VSS SS_VDD_MEDIA_IN_VSS SS_VDD_MEDIA_VSS
    ALL_ON SW_OFF ACC_OFF PERI_OFF MEDIA_OFF COMPUTE_ONLY IO_STANDBY MEDIA_MODE DEEP_SLEEP
  } {
    if {[string first $token $connectivity_text] < 0} {
      flow::fatal "loaded UPF is missing required supply, switch, or state token '$token'"
    }
  }
}

proc dc_upf_post_compile {} {
  global report_dir macro_cell_names

  if {[sizeof_collection [get_cells -hierarchical -quiet *u_power_switch_macro*]] != 0} {
    flow::fatal "compiled hierarchy contains forbidden power-switch macro instance"
  }
  set unmapped [get_cells -hierarchical -quiet -filter "is_hierarchical == false && is_unmapped == true"]
  foreach_in_collection cell $unmapped {
    set ref [get_attribute $cell ref_name]
    if {[lsearch -exact $macro_cell_names $ref] < 0} {
      flow::fatal "unexpected unmapped leaf [get_object_name $cell] ref=$ref"
    }
  }
  set bad_generic [get_cells -hierarchical -quiet -filter "ref_name =~ GTECH* || ref_name =~ SEQGEN*"]
  if {[sizeof_collection $bad_generic] != 0} {
    flow::fatal "mapped digital design contains GTECH/SEQGEN cells"
  }

  set els_cells [get_cells -hierarchical -quiet -filter "ref_name =~ upf_dc_demo_els_*"]
  set iso_cells $els_cells
  set pure_ls_cells [get_cells -hierarchical -quiet -filter "ref_name =~ upf_dc_demo_ls_*"]
  set ls_cells [add_to_collection $pure_ls_cells $els_cells]
  set lp_audit [open [file join $report_dir inserted_low_power_cells.rpt] w]
  puts $lp_audit "INSERTED_ISOLATION_COUNT=[sizeof_collection $iso_cells]"
  puts $lp_audit "INSERTED_LEVEL_SHIFTER_COUNT=[sizeof_collection $ls_cells]"
  puts $lp_audit "INSERTED_PURE_HL_LS_COUNT=[sizeof_collection $pure_ls_cells]"
  puts $lp_audit "PROVISIONAL_EXPECTED_ELS=36"
  puts $lp_audit "PROVISIONAL_EXPECTED_PURE_HL_LS=44"
  puts $lp_audit "NOTE=Provisional structural estimates are not synthesis acceptance assertions"
  foreach_in_collection cell $iso_cells {
    puts $lp_audit "ISO_CELL=[get_object_name $cell] REF=[get_attribute $cell ref_name]"
  }
  foreach_in_collection cell $ls_cells {
    puts $lp_audit "LS_CELL=[get_object_name $cell] REF=[get_attribute $cell ref_name]"
  }
  close $lp_audit
  if {[sizeof_collection $iso_cells] == 0} {
    flow::fatal "no mapped switchable-output ELS cells were inserted"
  }
  if {[sizeof_collection $pure_ls_cells] == 0} {
    flow::fatal "no mapped AO-to-domain H2L cells were inserted"
  }

  set mv_fd [open [file join $report_dir mv_check.rpt] r]
  set mv_text [read $mv_fd]
  close $mv_fd
  foreach pattern {
    {Found [1-9][0-9]* pin to pin connections requiring level shifter}
    {Found [1-9][0-9]* net\(s\) without isolation}
    {UPF-048} {MV-046} {\(MV-229\)} {UPF-814} {UPF-707a}
    {doesn't match -applies_to_boundary filter}
  } {
    if {[regexp -nocase $pattern $mv_text]} {
      flow::fatal "unresolved MV diagnostic: $pattern"
    }
  }
}

proc dc_upf_post_write {} {
  global netlist upf_out macro_pg_paths

  set netlist_fd [open $netlist r]
  set netlist_text [read $netlist_fd]
  close $netlist_fd
  foreach supply_name {
    VDD_AO VDD_PLL VDD_MEM VDDIO
    VDD_SW_IN VDD_SW VDD_ACC_IN VDD_ACC VDD_PERI_IN VDD_PERI
    VDD_MEDIA_IN VDD_MEDIA VSS
  } {
    if {[string first $supply_name $netlist_text] >= 0} {
      flow::fatal "non-PG netlist contains forbidden supply name '$supply_name'"
    }
  }
  foreach pg_pin {VDD VSS VDDIO VSSIO VGND VPWR VPWRIN LOWLVPWR VNB VPB VDDH VDDL VNW VPW} {
    set pg_pin_pattern [format {\.%s[[:space:]]*\(} $pg_pin]
    if {[regexp $pg_pin_pattern $netlist_text]} {
      flow::fatal "non-PG netlist contains forbidden named PG-pin connection '$pg_pin'"
    }
  }
  if {[string first "u_power_switch_macro" $netlist_text] >= 0} {
    flow::fatal "non-PG netlist contains forbidden power-switch macro instance"
  }
  set els_count [regexp -all -line {^[[:space:]]*upf_dc_demo_els_lh_1v2_1v8[[:space:]]+} $netlist_text]
  set hl_count [regexp -all -line {^[[:space:]]*upf_dc_demo_ls_hl_1v8_1v2[[:space:]]+} $netlist_text]
  puts "DC measured non-PG low-power cells: ELS=$els_count pure_HL_LS=$hl_count"

  set saved_upf_fd [open $upf_out r]
  set saved_upf_text [read $saved_upf_fd]
  close $saved_upf_fd
  foreach upf_token {
    {create_power_switch PSW_SW}
    {-input_supply_port {TVDD VDD_SW_IN}}
    {-output_supply_port {VDD VDD_SW}}
    {-control_port {NSLEEPIN u_aon_ctrl/sw_en_o}}
    {-on_state {normal TVDD {NSLEEPIN}}}
    {create_power_switch PSW_ACC}
    {-input_supply_port {TVDD VDD_ACC_IN}}
    {-output_supply_port {VDD VDD_ACC}}
    {-control_port {NSLEEPIN u_acc_aon_ctrl/sw_en_o}}
    {create_power_switch PSW_PERI}
    {-input_supply_port {TVDD VDD_PERI_IN}}
    {-output_supply_port {VDD VDD_PERI}}
    {-control_port {NSLEEPIN u_peri_aon_ctrl/sw_en_o}}
    {create_power_switch PSW_MEDIA}
    {-input_supply_port {TVDD VDD_MEDIA_IN}}
    {-output_supply_port {VDD VDD_MEDIA}}
    {-control_port {NSLEEPIN u_media_aon_ctrl/sw_en_o}}
  } {
    if {[string first $upf_token $saved_upf_text] < 0} {
      flow::fatal "saved UPF is missing abstract power-switch clause '$upf_token'"
    }
  }
  foreach forbidden_switch_token {
    upf_dc_demo_power_switch_macro u_power_switch_macro/VIN
    u_power_switch_macro/VOUT u_power_switch_macro/VSS map_power_switch
  } {
    if {[string first $forbidden_switch_token $saved_upf_text] >= 0} {
      flow::fatal "saved UPF contains forbidden switch implementation token '$forbidden_switch_token'"
    }
  }
  foreach pin_path $macro_pg_paths {
    if {[string first $pin_path $saved_upf_text] < 0} {
      flow::fatal "saved UPF is missing macro PG path '$pin_path'"
    }
  }
  foreach state_name {
    ALL_ON SW_OFF ACC_OFF PERI_OFF MEDIA_OFF COMPUTE_ONLY IO_STANDBY MEDIA_MODE DEEP_SLEEP
  } {
    if {[string first $state_name $saved_upf_text] < 0} {
      flow::fatal "saved UPF is missing system power state '$state_name'"
    }
  }
}
