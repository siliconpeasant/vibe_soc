# Third-party / foundry lint waivers.
# In-house RTL must be fixed, not waived.
#
# Policy approved 2026-08-14.
# Source this after check_lint. VC Static uses waive_lint / waive_violation,
# not a bare "waive" command.

proc vc_waive_third_party {name tag filter} {
  set comment "third-party/foundry waiver policy 2026-08-14"
  if {[llength [info commands waive_lint]] > 0} {
    if {[catch {
      waive_lint -add $name -tag $tag -filter $filter -comment $comment
    } err]} {
      puts "VC_STATIC: waive_lint failed ($name $tag): $err"
    } else {
      puts "VC_STATIC: waived $tag via waive_lint ($name)"
    }
    return
  }
  if {[llength [info commands waive_violation]] > 0} {
    if {[catch {
      waive_violation -app lint -add $name -tag $tag -filter $filter \
        -status waived -comment $comment
    } err]} {
      puts "VC_STATIC: waive_violation failed ($name $tag): $err"
    } else {
      puts "VC_STATIC: waived $tag via waive_violation ($name)"
    }
    return
  }
  puts "VC_STATIC: waive_lint/waive_violation unavailable; skip $name"
}

# Nangate45 ICG primitive model (latch is the stdcell; SYNTHESIS stub
# does not read CK/E/SE because Liberty binds the cell).
vc_waive_third_party tp_icg_inferlatch InferLatch {FileName=~"*CLKGATETST_X1.v"}
vc_waive_third_party tp_icg_w240       W240       {FileName=~"*CLKGATETST_X1.v"}

# OpenTitan prim
vc_waive_third_party tp_prim_fifo_rst  STARC05-1.3.1.3 {FileName=~"*prim_fifo_async.sv"}
vc_waive_third_party tp_prim_fifo_w528 W528            {FileName=~"*prim_fifo_async.sv"}
vc_waive_third_party tp_prim_sync_w528 W528            {FileName=~"*prim_flop_2sync.sv"}

# PULP CIC / third_party
vc_waive_third_party tp_varcic_rio  RegInputOutput-ML {FileName=~"*varcic.sv"}
vc_waive_third_party tp_varcic_w528 W528              {FileName=~"*varcic.sv"}

# DesignWare DW_axi_dmac generated vendor RTL (coreConsultant source).
vc_waive_third_party tp_dw_dmac_vendor_star  STARC05-1.3.1.3 {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_w528  W528            {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_w240  W240            {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_w416  W416            {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_w415  W415a           {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_fec   FlopEConst      {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_vendor_infer InferLatch      {FileName=~"*vendor/dw_axi_dmac*"}
vc_waive_third_party tp_dw_dmac_tpram_w528   W528            {FileName=~"*tpram_64d32w_beh.v"}
vc_waive_third_party tp_dw_dmac_tpram_rst    STARC05-1.3.1.3 {FileName=~"*tpram_64d32w_beh.v"}
vc_waive_third_party tp_dw_dmac_if_w528      W528            {FileName=~"*dw_axi_dmac_fifo_mem_if.v"}

# Generated Nangate FakeROM/FakeRAM behavioral models (hard-macro stand-in).
vc_waive_third_party tp_fakerom_w123   W123              {FileName=~"*fakerom45*"}
vc_waive_third_party tp_fakerom_undrv  UndrivenInTerm-ML {FileName=~"*fakerom45*"}
vc_waive_third_party tp_fakerom_w528   W528              {FileName=~"*fakerom45*"}
vc_waive_third_party tp_fakerom_rst    STARC05-1.3.1.3   {FileName=~"*fakerom45*"}
vc_waive_third_party tp_fakeram_w123   W123              {FileName=~"*fakeram45*"}
vc_waive_third_party tp_fakeram_undrv  UndrivenInTerm-ML {FileName=~"*fakeram45*"}
vc_waive_third_party tp_fakeram_w528   W528              {FileName=~"*fakeram45*"}
# CE-gated behavioral array: M1 leaves NPU workspace req unused (const0 at top).
vc_waive_third_party tp_fakeram_flopec FlopEConst        {FileName=~"*fakeram45*"}
