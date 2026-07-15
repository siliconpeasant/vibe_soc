# Synthesis and PD gate

Synthesis uses registered `soc-build.soc_syn` with the complete filelist and
explicit RTL top. Close `syn` only with immutable run evidence and non-empty
log/netlist artifacts. Structural synthesis is not timing closure; claim timing
only from a real STA report with WNS/TNS.

If synthesis repairs RTL, complete the final synthesis and invalidate
verification once. Follow the RTL-epoch rule if verification already owns
repair.

Physical design uses `soc-openroad_init`, `soc_openroad_run`, and
`soc_openroad_status`. Design-owned handoff files live under `pd/openroad/`;
external ORFS/OpenROAD trees remain separate. Require `de/run/rtl.f` as the RTL
handoff source and do not add a `pd` pipeline stage. Tool or report absence is a
blocker, never a shell fallback or estimated result.
