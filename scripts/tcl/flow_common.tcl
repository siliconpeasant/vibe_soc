# Shared Tcl helpers for registered synthesis, Formality, and CLP flows.

namespace eval flow {
  variable fatal_prefix "FLOW_FATAL"
}

proc flow::set_fatal_prefix {prefix} {
  variable fatal_prefix
  set fatal_prefix $prefix
}

proc flow::env_or {name default_value} {
  if {[info exists ::env($name)] && $::env($name) ne ""} {
    return $::env($name)
  }
  return $default_value
}

proc flow::env_required {name} {
  set value [flow::env_or $name ""]
  if {$value eq ""} {
    flow::fatal "required environment variable '$name' is unset"
  }
  return $value
}

proc flow::fatal {message} {
  variable fatal_prefix
  puts stderr "$fatal_prefix: $message"
  exit 2
}

proc flow::require_file {path} {
  if {$path eq "" || ![file exists $path] || [file size $path] == 0} {
    flow::fatal "missing or empty input: $path"
  }
}

proc flow::split_words {value} {
  if {$value eq ""} {
    return {}
  }
  return [regexp -all -inline {\S+} $value]
}

proc flow::bool_enabled {value} {
  return [expr {
    [string match -nocase "1" $value] ||
    [string match -nocase "true" $value] ||
    [string match -nocase "yes" $value]
  }]
}

proc flow::require_command {name} {
  if {[llength [info commands $name]] == 0} {
    flow::fatal "required command '$name' is unavailable"
  }
}

proc flow::required_report {path command_words} {
  set command_name [lindex $command_words 0]
  flow::require_command $command_name
  if {[catch {redirect -file $path {uplevel #0 $command_words}} message]} {
    flow::fatal "report '$command_name' failed: $message"
  }
  flow::require_file $path
}

proc flow::require_filelist {filelist} {
  flow::require_file $filelist
  set fd [open $filelist r]
  set has_entry false
  foreach raw_line [split [read $fd] "\n"] {
    set line [string trim $raw_line]
    if {$line eq "" || [string match "#*" $line] || [string match "//*" $line]} {
      continue
    }
    set has_entry true
    break
  }
  close $fd
  if {!$has_entry} {
    flow::fatal "no RTL entries in $filelist"
  }
  return $filelist
}

proc flow::source_optional {path label} {
  if {$path eq ""} {
    return
  }
  flow::require_file $path
  if {[catch {uplevel #0 [list source $path]} message]} {
    flow::fatal "$label failed: $message"
  }
}

proc flow::run_hook {name} {
  if {[llength [info commands $name]] > 0} {
    if {[catch {uplevel #0 [list $name]} message]} {
      flow::fatal "hook '$name' failed: $message"
    }
  }
}
