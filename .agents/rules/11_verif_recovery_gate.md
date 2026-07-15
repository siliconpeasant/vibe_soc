# Verification recovery

Compile, simulation, regression, and coverage use registered `soc-build`
tools. A successful `soc_sim` already includes compilation.

On failure, inspect the real log first and classify environment/tool, filelist
or elaboration, RTL behavior, testbench expectation, timeout, or
license/resource. Record the failed check and remediation when pipeline state is
in scope, then return to the earliest affected stage. Do not dispatch downstream
work from failed or stale evidence.

Verification passes only when the registered run completes, its immutable log
contains the project pass condition, and error/fatal counters are clean. A
timeout, partial/stale log, or appended PASS marker is not evidence.

If verification repairs RTL, finish simulation on the final source and
invalidate synthesis once. Follow the RTL-epoch rule if synthesis already owns
repair.
