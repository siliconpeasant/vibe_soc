# Place top pins then the SPM blackbox macro before detailed floorplan steps.
if { [llength [info commands place_pins]] > 0 } {
  place_pins -hor_layers metal3 -ver_layers metal2
  puts "Info: placed top-level pins on metal2/metal3."
}

set block [ord::get_db_block]
set core [$block getCoreArea]
set core_llx [ord::dbu_to_microns [$core xMin]]
set core_lly [ord::dbu_to_microns [$core yMin]]

set placed 0
foreach inst [$block getInsts] {
  set master [$inst getMaster]
  if { $master == "NULL" } { continue }
  set mname [$master getName]
  if { $mname eq "stories260k_spm" } {
    # Flush to core lower-left. A small leftover gap (e.g. +10 um) creates a
    # ~8 um site strip that cannot hold BUF_X32 (9.31 um) after row cut, and
    # repair_design long-wire buffers then fail detailed_placement (DPL-0036).
    set x $core_llx
    set y $core_lly
    $inst setOrigin [ord::microns_to_dbu $x] [ord::microns_to_dbu $y]
    $inst setOrient R0
    $inst setPlacementStatus FIRM
    puts "Info: placed SPM macro [$inst getName] at ($x, $y) (flush core LL)"
    incr placed
  }
}
puts "Info: placed $placed SPM macro instance(s)"
