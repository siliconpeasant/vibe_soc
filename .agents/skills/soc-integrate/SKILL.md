---
name: soc-integrate
description: Extract RTL ports, generate instances/wrappers/top modules, check connections, and refresh named instances from current RTL with optional tracking.
---

# SoC Integrate

Agents must use the registered `soc-integrate` MCP server and must not invoke
the Python CLI as a fallback. CLI examples below are for development/testing only.

Tools:

- `soc_extract`, `soc_instantiate`, `soc_wrap`, `soc_csv`
- `soc_integrate`, `soc_check`, `soc_extract_map`, `soc_update`, `soc_remove`
- `soc_snapshot`, `soc_diff`

## Outputs and refresh

`soc_integrate` writes the top and prints check results. **Both sidecars default
off**: `csv=True` / `--csv` requests `<top>.integrate.csv`; `track=True` / `--track`
requests `<top>.integrate.json`, including a `checks` array. They are independent.
`soc_csv` remains an explicit module-port CSV export. Every text output ends in a
newline. Sidecars already present are not deleted or refreshed unless requested.

```bash
python3 scripts/soc_integrate.py integrate a.sv b.sv -n top -o top.sv --map ports.json
python3 scripts/soc_integrate.py update top.sv --files a.sv b.sv
python3 scripts/soc_integrate.py diff top.sv --files a.sv b.sv
python3 scripts/soc_integrate.py check top.sv --files a.sv b.sv --strict
python3 scripts/soc_integrate.py extract-map top.sv -o ports.json
```

Paths above are relative to this skill directory. `soc_update(top_file=...,
module_files=[...])` reads actual instance names, named parameter overrides and
named port expressions from the existing top. It preserves each surviving
connection expression verbatim, adds current ports using the shared/map rules,
removes deleted ports, and rebuilds top ports/wires. Surviving top ports keep their
existing header order; new top ports are appended. Existing connections take
precedence over a supplied map; maps provide defaults for newly added ports.
It reports `[NEW]`, `[DEL]`, and `[MOD]` per instance. Neither update, diff-from-top,
nor extract-map requires JSON. Update accepts the legacy `config_file` JSON form
as well. `soc_remove` accepts a tracked config or generated top.

Generated tops carry a `// soc-integrate:` metadata comment containing the prior
interface and original map rules. This lets width/direction/type changes and
templates survive without a sidecar. Connections are always read from RTL, not
from that comment. Without prior metadata, additions/deletions are detectable;
old internal port directions/widths cannot generally be recovered. Provide
current RTL with `--files` (MCP `module_files`); generated source paths are an
optional convenience. Snapshot-based `diff module.sv snapshot.json` and spec
`check module.sv spec.json` remain available. Refresh owns generated declarations
and instances: arbitrary hand-written top logic is outside its supported scope.

## Maps and templates

Legacy exact module keys still work: `{"mappings":{"consumer.data_i":"q"}}`.
The preferred keys use instance names, allowing repeated instances of a module.
For repeated instances supply an `instances` list as in this example:

```json
{
  "instances": [
    {"module": "dma", "instance": "u_dma0"},
    {"module": "dma", "instance": "u_dma1"}
  ],
  "mappings": {
    "u_dma1.irq_o": "special_irq",
    "u_dma0.enable": "1'b0",
    "u_dma0.status_o": null
  },
  "templates": [
    {"regex": "u_dma(\\d+)\\.irq_o", "value": "dma_irq[$1]"},
    {"glob": "u_*.reset_n", "value": "rst_$1_n"}
  ]
}
```

Precedence is exact `instance.port`, then exact legacy `module.port`, then the
first matching template. Ordered patterns embedded in `mappings` precede the
`templates` list; JSON object/list order is preserved. Patterns match the entire
`instance.port`. Use `regex:` or `glob:` key prefixes; legacy keys containing
parentheses/backslashes infer regex and keys containing `*`/`?` infer glob.
Regex follows Python `re` syntax. Glob captures each `*` (zero or more characters)
and `?` (one character); other characters, including brackets, are literal.
`$1`, `$2`, etc. substitute captured groups. Values can be signal expressions or
objects such as `{"signal":"data","clock":"clk_a","sync":true}`. Objects containing only `clock`/`sync` annotations keep the default connection;
put annotations in `annotations` when they should apply independently of mappings.

Selections (`sig[7:4]`, `sig[3]`) are explicit connections; the parent bus is
declared large enough for numeric indices. Constants (`1'b0`, `'0`, `8'hFF`, `'1`)
are valid input tie-offs. `null` and `""` emit `.port()`: outputs report unused;
inputs warn as undriven and should instead receive a constant when tied off.
Generated empty connections are individually enclosed in Verilator
`lint_off PINCONNECTEMPTY` / `lint_on PINCONNECTEMPTY` comments. These comments
acknowledge the explicit mapping without suppressing the soc-integrate checks.
Constants on outputs/inouts are errors. No automatic truncation/extension or
implicit slicing is performed.

Unmapped same-name inputs share an external input only when their normalized
resolved widths, type text and unpacked dimensions match. One compatible output
plus inputs connects through an internal net. Normalization treats implicit
wires and wire/reg/logic storage as the same four-state value type; signedness
and named/package types remain distinct. Incompatible candidates are exposed
separately with a module prefix and an `auto-share-incompatible` warning, so users
can map explicitly. Otherwise unique ports are exposed with a module prefix.
Explicit maps can share otherwise different names. Inspect the generated wiring:
names alone do not establish protocol compatibility.

`extract-map` retains templates from the top's metadata and adds exact keys only
for unmapped/manual connections. `--expand` (MCP `expand=True`) explicitly
materializes all instance-port keys. Rules are never expanded by default.

## Checks

Integration, update and top `check` report structured warnings for known width
mismatches, unknown widths, overlapping multiple drivers, unconnected inputs,
unused/unconnected outputs, and inferred CDC crossings. Exposed top inputs are
external drivers; exposed top outputs are external consumers, so neither is
reported as floating merely because there is no other child endpoint. CSV
`Shared_With` lists actual other `instance.port` endpoints on the same net,
including clocks, resets and internal nets; `Checks` lists associated warning
codes. The tracking JSON stores the full check results. `--strict` (MCP
`strict=True`) makes warnings fail with nonzero status before any output write.
Port-spec checks always fail for missing/extra/modified ports.

Clock inference recognizes `clk`, `clk_*`, `*_clk`, and `*_clk_i`/`*_clk_o` and
uses their connected signal names as domains. Override with per-port
`annotations`, mapping value objects, or `domains` keyed by instance (then
module). Multi-clock sinks need a per-port clock; ambiguous domains warn.
For example:

```json
{
  "annotations": {"u_dma.data_i": {"clock": "clk_a", "sync": true}},
  "domains": {"u_cpu": "clk_a", "u_io": {"data_i": "clk_b"}},
  "synchronizers": ["u_io.async_i", "u_sync"]
}
```

`clock` may name a child clock port (resolved to its connected net) or an
explicit domain label. `sync:true`, a sink endpoint, or a sink instance in
`synchronizers` declares an intentional synchronizer. These are heuristic
connectivity checks, not CDC/RDC, protocol, electrical or timing signoff. Review
clock/reset-domain and synchronizer intent with the relevant signoff tools.

## Parser and limits

Supports ANSI continuations, non-ANSI ordered headers plus body direction
statements, wire/reg/logic, signedness, multiple names, packed/unpacked dimensions,
output storage redeclarations, header/body parameters and body localparams.
Extraction preserves symbolic widths and defaults. Generated concrete dimensions
simplify constant integer arithmetic (`[WIDTH-1:0]` with WIDTH=8 becomes `[7:0]`);
symbolic dimensions remain symbolic. Wrappers forward public parameters;
localparams never become instance overrides. Package/user-defined type text is
preserved verbatim in declarations; package-qualified or `_t` value types may
omit the input direction. Provide package/typedef sources to the HDL
tool. Unknown type widths produce a check warning rather than a guessed width.

Native interface/modport ports (`bus_if s`, `bus_if.slave s`) generate internal
`bus_if s ();` instances and connect `.s(s)`. Map endpoints to the same interface
name to connect peers. Supply interface definitions separately to your HDL tool.
Modports are retained in child metadata; the interface declaration uses the base
type. Parameterized interface declarations, interface arrays, inline aggregates,
default-valued ports, positional/wildcard instance connections and instance
arrays/multiple instances per statement are unsupported and fail explicitly.
The parser is not a complete SystemVerilog elaborator; it does not parse package
bodies to compute typedef widths or determine interface parameters. Unsupported
port declarations report a file, line and construct rather than dropping ports.

All RTL-reading tools accept `include_dirs`/`defines` (CLI repeated `-I dir`,
`-D NAME[=value]`, `+incdir+dir+dir`, `+define+NAME=value+NAME`). Include lookup
searches the containing directory then include directories. Object-like defines,
macro substitution, nested ifdef/ifndef/elsif/else/endif and undef are supported.
Missing includes, undefined/recursive/function-like macros, malformed conditionals
and unsupported interface syntax are explicit errors. This is not a replacement
for a full compiler preprocessor.
