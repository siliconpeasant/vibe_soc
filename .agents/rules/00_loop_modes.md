# Loop execution modes

The loop separates fast development from delivery closure. Run
`.agents/scripts/loop_context.py <workspace>` before loading stage contracts.
The generated compact packet is the routing source of truth for the current
diff; read only the rules listed in that packet.

## Modes

| Mode | Purpose | Required behavior |
|---|---|---|
| `dev` | Single-module inner loop | Use one RTL stage owner, keep `rtl` open as `in_progress`, run registered targeted lint/compile/simulation, and defer synthesis and independent review. Do not claim pipeline closure. |
| `merge` | Final diff before PR/merge | Settle documentation, close `rtl`, run final registered verification and synthesis once, then run `soc-reviewer normal`. |
| `signoff` | High-risk integration/implementation work | Run the complete gated flow plus applicable CDC, timing, low-power, integration, or PD checks and `soc-reviewer strict`. |

`LOOP_MODE` or `--mode` requests a minimum mode. The router may automatically
escalate `dev -> merge -> signoff`; a caller cannot force a lower mode than the
detected risk. Filelists and verification collateral escalate to at least
`merge`. Interfaces, registers, clocks/resets, constraints, generated
tops/wrappers, chip-top RTL, multi-module edits, UPF, and PD collateral escalate
to `signoff`.

## Development contract

For material RTL work in `dev`, reopen or start `rtl in_progress` once before
editing. Multiple iterations may remain in that state. Record real targeted MCP
results in the task report or transient `de/run/loop_evidence/`; they are useful
development evidence but do not satisfy `rtl`, `verif`, or `syn` delivery
closure. A failing targeted check stops the inner loop until repaired.

For documentation-only development, keep `doc in_progress`, run the document
delta check, and defer downstream closure. Do not open `rtl` solely for a
documentation edit.

Before delivery, rerun the router with `--mode merge`. Complete the returned
stale or pending stages with registered MCP tools and run the mapped reviewer.
After a passing review, rerun with `--review-result pass --check-ready`. A
`signoff` delivery also supplies `--risk-checks-passed` only after its selected
registered checks pass. Fingerprint reuse is allowed only when the compact
packet marks the stage fresh; deferred checks are never treated as passes.

Direct EDA shell fallbacks remain forbidden in every mode. Timing, verification,
synthesis, and physical-design success still require real registered-tool
evidence.
