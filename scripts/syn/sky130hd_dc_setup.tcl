# SkyWater SKY130 HD setup for Design Compiler.
# Keep machine-specific paths in scripts/local.mk or environment variables.
# Prefer SKY130HD_DC_DB when a Synopsys .db has been generated with Library Compiler.

proc sky130hd_env_or {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} {
    return $::env($name)
  }
  return $default_value
}

set sky130hd_db  [sky130hd_env_or SKY130HD_DC_DB ""]
set sky130hd_lib [sky130hd_env_or SKY130HD_DC_LIB ""]

if {$sky130hd_db ne ""} {
  if {![file exists $sky130hd_db]} {
    puts stderr "SKY130HD_DC_DB does not exist: $sky130hd_db"
    exit 2
  }
  set_app_var target_library [list $sky130hd_db]
  set_app_var link_library [concat [list *] [get_app_var target_library]]
} elseif {$sky130hd_lib ne ""} {
  if {![file exists $sky130hd_lib]} {
    puts stderr "SKY130HD_DC_LIB does not exist: $sky130hd_lib"
    exit 2
  }
  puts "WARNING: SKY130HD_DC_LIB is a Liberty file. If this DC install requires .db target libraries, compile it with Library Compiler and set SKY130HD_DC_DB."
  set_app_var target_library [list $sky130hd_lib]
  set_app_var link_library [concat [list *] [get_app_var target_library]]
} else {
  puts stderr "Set SKY130HD_DC_DB to a compiled Sky130HD .db, or SKY130HD_DC_LIB to a Sky130HD Liberty .lib."
  exit 2
}
