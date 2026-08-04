# SoC RTL coding contract

The approved interface/design specification and existing repository style take precedence. Defaults apply only when the project is silent.

**Detailed project standard (open when writing or reviewing RTL):**
`.agents/rules/04_verilog_coding_style.md` (M mandatory / S should / R recommend).

## Language and structure

- Default to synthesizable Verilog-2005; use SystemVerilog only when the project explicitly does.
- Match module and filename and use lower_snake_case identifiers.
- Use parameters for supported configuration and localparams for derived constants.
- Give combinational blocks complete assignments; inferred latches require an explicit reviewed design reason.
- Make width extension, truncation, signedness, clock-domain crossings, and reset crossings explicit.
- Do not suppress lint warnings solely to make a gate pass.

## Clock and reset

- Implement reset polarity and synchronous/asynchronous behavior exactly as specified; do not impose a global reset style that contradicts the approved design.
- If the design is silent, follow S.DFF / S.CRG in `04_verilog_coding_style.md`.
- Every state element must have intentional reset/initialization behavior documented in the design specification.
- Generated clocks, clock muxes/gates, and reset synchronizers use reviewed library wrappers or the CRG generator, not ad-hoc logic.

## Canonical layout

| Path | Content |
|---|---|
| `de/rtl/` | synthesizable `.v`/`.sv` and `filelist.f|mk` |
| `de/syn/` | SDC, netlist and synthesis/STA reports |
| `de/run/` | transient lint/build output |
| `dv/tb/` | testbench source |
| `dv/sim/` | transient simulation logs, images and waves |

Comments explain non-obvious intent, constraints, invariants, or workarounds. Avoid boilerplate comments that merely restate code.
