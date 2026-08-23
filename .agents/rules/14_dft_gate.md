# DFT frontend gate

Use when the packet owns scan/test-mode readiness, DFT SGDC/Tcl, or SpyGlass DFT.

## Owner

- **`soc-dft-engineer`** owns DFT readiness, `de/dft/` collateral, and
  `soc_dft` SpyGlass runs.
- RTL port/mux fixes return to **`soc-rtl-designer`** (or CRG/integrator for
  clock/reset/test distribution ownership).
- DFT is a **side lane**, not a `pipeline_state.json` stage. Do not close
  `rtl`/`verif`/`syn` solely from DFT evidence.

## Required inputs

- Module workspace with synthesizable RTL and a known `RTL_TOP`
- Project filelist path used by Make (`de/run/rtl.f` after flist)
- Project DFT frontend standard when available (packet link or local copy)
- Optional reviewed waiver (`.awl`) under `de/dft/`

## Checks

| Check | Tool | Pass criteria |
|---|---|---|
| DFT hooks reserved | `dft-gen.dft_readiness_check` | Required categories present or explicitly waived/N/A with note |
| SGDC/Tcl present | `dft-gen.dft_sgdc_gen` / `dft_tcl_gen` | Non-empty `de/dft/*_dft.sgdc` (+ driver Tcl when used) |
| SpyGlass DFT | `soc-build.soc_dft` | Real moresimple/report under `de/run/dft/`; no invent PASS |

Default SpyGlass goal: `dft/dft_scan_ready`. Optional
`dft/dft_best_practice` only when requested.

## SGDC content expectations

Reviewed SGDC should declare, as applicable:

- `current_design <top>`
- `test_mode -name <path> -value <0|1>`
- `reset -name <path> -value <0|1>` for functional and **test** resets
  (`test_rstn`, `dft_*rst*`, `dftrstdisable*`, …)
- `clock -name <path> ...` and test clocks (`-atspeed -testclock` when required)

Starter generators may emit top-level port-only SGDC. Hierarchical full-chip
paths remain a reviewed hand-edit or YAML source of truth.

## Fail / blocked

- Missing must-have test_mode / scan enable / test reset when the standard
  requires them → readiness **fail**, not silent skip
- Missing SpyGlass binary or DFT license → **blocked** with remediation; keep
  SGDC generation results
- Treating `dft_scan_ready` alone as ATPG/MBIST/LBIST signoff → invalid claim

## Do not

- Bypass registered MCP (`soc_dft` / `dft-gen`) with ad-hoc `sg_shell`
- Claim DFT PASS from logs that predate the current RTL fingerprint
- Expand scope into functional verification, synthesis, or PD
