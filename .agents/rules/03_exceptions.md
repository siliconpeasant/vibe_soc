# Loop exceptions and escalation

Do not use line count or the words "bug" and "feature" to choose a flow. Run
`loop_context.py`; its selected mode is authoritative.

- Comment, formatting, and documentation-only changes use the closest relevant
  non-EDA validation and do not reopen RTL stages.
- A single-module RTL fix or feature may iterate in `dev`, with one RTL stage
  owner and targeted registered checks. Synthesis and independent review are
  deferred, not waived.
- Filelist, verification-collateral, or delivery-manifest changes use at least
  `merge`.
- New modules, interface/parameter/register changes, cross-module work,
  clocks/resets, constraints, generated tops/wrappers, chip-top RTL, UPF, and PD
  work use `signoff`.

An approved doc-stage skip remains available only when the existing interface
and behavior contract is unchanged. Record the reason in `pipeline_state.json`
before RTL closure. No exception permits direct EDA shell fallback or fabricated
PASS/timing evidence.
