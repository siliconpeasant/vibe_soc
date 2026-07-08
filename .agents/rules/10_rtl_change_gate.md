# RTL change gate

Use this rule to decide whether a task must enter the gated module pipeline.

## Material RTL changes

Treat a task as a material RTL change when it modifies or creates any of:

- synthesizable Verilog/SystemVerilog under `de/rtl/`
- RTL filelists or composition logic such as `filelist.f`, `filelist.mk`, or generated `de/run/rtl.f`
- module interfaces, clocks, resets, bus wiring, register-visible behavior, or top-level integration
- synthesis constraints or handoff assumptions under `de/syn/`
- generated top, wrapper, register-file, or CRG artifacts

Material RTL changes require the gated `doc -> rtl -> {verif, syn}` flow unless an existing rule grants a documented exception.

## Lightweight changes

Do not reopen the full pipeline for comment-only edits, documentation-only edits, formatting that does not change generated filelists or elaborated RTL, or test-manifest edits that do not affect RTL content. Still run the closest relevant validation and record the command/tool used in the final response.

## Required preflight

Before editing material RTL:

1. Read `01_swarm_flow.md`, `02_toolchain.md`, and `05_pipeline_state.md`.
2. Read `04_coding_style.md` before manual RTL edits.
3. Read `06_design_knowledge.md` and query `soc-ai-kb` before design decisions when available.
4. Query the module `pipeline_state.json`; initialize it only when absent.
5. Mark the owned stage `in_progress` before stage work starts.

## Closure

Close a material RTL stage only after artifacts exist, registered MCP checks pass, and `pipeline_state.json` records the result. If verification or synthesis repairs RTL, follow the downstream invalidation rules in `01_swarm_flow.md` and `05_pipeline_state.md`.
