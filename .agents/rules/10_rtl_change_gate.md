# RTL change gate

Material changes include synthesizable RTL, RTL/filelist composition,
interfaces, clocks/resets, register-visible behavior, synthesis constraints,
generated tops/wrappers/register files/CRG, and chip integration. They enter the
module pipeline.

One low-risk module may iterate in `dev` with `rtl in_progress`. Interface,
register, clock/reset, constraint, generated-top, chip-top, multi-module,
low-power, or PD impact escalates to `signoff`. Delivery closes the final
snapshot once; it does not replay every intermediate edit.

Comment/formatting changes, non-behavioral documentation, and test manifests
that do not alter RTL are lightweight. Run the nearest parser/checker without
reopening the RTL pipeline.

Before material editing, use the router packet, read only its rules, and start
the owned stage. In delivery modes, close RTL only with current artifacts and
registered checks. Reuse downstream evidence only when the packet marks it
fresh.
