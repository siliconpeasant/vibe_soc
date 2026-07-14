# RTL change gate

Use this rule to decide whether a task must enter the gated module pipeline.

## Material RTL changes

Treat a task as a material RTL change when it modifies or creates any of:

- synthesizable Verilog/SystemVerilog under `de/rtl/`
- RTL filelists or composition logic such as `filelist.f`, `filelist.mk`, or generated `de/run/rtl.f`
- module interfaces, clocks, resets, bus wiring, register-visible behavior, or top-level integration
- synthesis constraints or handoff assumptions under `de/syn/`
- generated top, wrapper, register-file, or CRG artifacts

Material RTL changes enter the Loop. A low-risk, single-module change may use
`dev` for repeated edits, but it must remain `rtl in_progress` and cannot claim
delivery closure. Before PR or delivery, `merge` closes the final
`doc -> rtl -> {verif, syn}` evidence once. Router-detected interface,
clock/reset, register, constraint, integration, generated-top, multi-module, or
PD risk automatically uses `signoff`.

## Lightweight changes

Do not reopen the full pipeline for comment-only edits, documentation-only edits, formatting that does not change generated filelists or elaborated RTL, or test-manifest edits that do not affect RTL content. Still run the closest relevant validation and record the command/tool used in the final response.

## Required preflight

Before editing material RTL:

1. Run `loop_context.py <workspace>` and use its selected mode.
2. Read only the rules listed in the compact packet, including coding style and design knowledge when selected.
3. Query compact module state; initialize it only when absent.
4. Mark the owned stage `in_progress` before stage work starts.

## Closure

Do not close a material RTL stage in `dev`. In `merge` or `signoff`, close it
only after artifacts exist, registered MCP checks pass, and state records the
current fingerprint. Reuse a downstream result only when the compact packet
marks it fresh. RTL repaired by verification or synthesis still follows the
downstream invalidation rules.
