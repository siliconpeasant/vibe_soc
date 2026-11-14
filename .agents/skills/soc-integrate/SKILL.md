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

`soc_integrate` writes the top. Warnings and the Checks summary go to stderr;
stdout carries the primary result or output paths. For CLI integration, `-n name`
defaults to `-o name.sv`; `-o path.sv` derives the top name from the file stem.
Omitting both is an error. **Both sidecars default
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
It reports `[NEW]`, `[DEL]`, and `[MOD]` per instance. A single deletion/addition
on the same module with equal direction and resolved bit count also reports
`[REN?] old -> new` and a suggested exact port-map entry retaining the former
connection. This is a suggestion; refresh does not rename connections automatically.
Review it before updating, or use `--strict` to stop before writing. A removed
child port that exposes its former internal net as a new top input/output reports
`removed-port-exposes-net`. Refresh/diff warn about stale exact port-map keys
(non-existent instances or ports); initial integration still rejects unknown
owners to catch typos. Non-existent ports on a known owner warn in all flows. Neither update, diff-from-top,
nor extract-map requires JSON. Update accepts the legacy `config_file` JSON form
as well. `soc_remove` accepts a tracked config or generated top. Its `module_name` may
name one instance or a module (removing all its instances). Unknown names fail
without writing. Matching exact map owners and templates used only by removed
endpoints are dropped; templates also used by surviving endpoints remain.
`output`, `strict` and `port_map` have the same meaning as on update.

Generated tops carry a `// soc-integrate:` metadata comment containing the prior
interface and original map rules. Version 2 stores each module interface once in
`modules`; `instances` reference the module name and store only parameter overrides.
Source paths are relative to the top file, so moving an identical source/top tree
produces identical metadata and supports implicit-source refresh from any working
directory. Original map/template precedence and source/instance order remain
stable. Legacy version 1 full-instance metadata (including absolute source paths)
is still readable and upgrades on refresh. This lets width/direction/type changes
and templates survive without a sidecar. Connections are always read from RTL, not
from that comment. Without prior metadata, additions/deletions are detectable;
old internal port directions/widths cannot generally be recovered. Provide
current RTL with `--files` (MCP `module_files`); generated source paths are an
optional convenience. Snapshot-based `diff module.sv snapshot.json` and spec
`check module.sv spec.json` remain available. Refresh owns generated declarations and named instances. Protect custom logic
with paired markers (multiple blocks are supported):

```systemverilog
// soc-integrate:user begin
wire custom_enable;
assign custom_enable = test_mode;
// soc-integrate:user end
```

Blocks are preserved verbatim by `update` and by `integrate -o` when regenerating
an existing top. Their contents are opaque to connection checks. Nested or
unmatched markers fail before writing. Unrecognized body text outside protected regions is preserved verbatim in an
automatically created user region, including declarations, assign/always logic,
unknown module instances, generate/preprocessor blocks, comments and functions/tasks.
Diff/check/update report `[preserved-unmanaged]` with the original file:line.
The next update is idempotent. The same preservation applies when regenerating
an existing generated top with `integrate -o`. Regeneration drops removed
tool-managed instances rather than preserving them as user text. Existing
non-generated files are refused unless `--force` (MCP `force=True`) is given;
force replaces that file. Conditional owned instances stay verbatim with their
wrapping and connections, participate in the connection graph, and report
`conditional-preserved`. Their nets retain declarations and are never promoted
merely because of conditional wrapping. Refresh does not rewrite their pins;
review conditional source when a child interface changes. Generated declarations carry ownership
metadata so new user declarations are not mistaken for generated nets.
Positional/wildcard connections, module instance arrays and duplicate pins on
managed instances still fail explicitly. Opaque user code is preserved, not elaborated.

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

Each `instances[]` entry may supply `parameters`, keyed by the child's public
parameter name. JSON integers emit decimal literals, booleans emit `1'b1` / `1'b0`,
and strings emit verbatim HDL expressions. For example:

```json
{"instances": [{"module": "tlul_socket_1n", "instance": "u_socket",
                "parameters": {"N": 2, "ExplicitErrs": true}}]}
```

`{"N":"2"}` and `{"N":"(1+1)"}` also select two devices. Unknown parameters,
localparam overrides and other JSON value types fail explicitly. Each configured
instance resolves its own parameter/localparam chains, packed bounds and unpacked
bounds; the shared default interface is unchanged. Integer arithmetic is folded
locally where supported. Named types and remaining expressions use Verilator
probes with `-G` overrides (locally evaluable expressions become literal `-G`
values). Verilator 5.032 only accepts literals with `-G`; expressions it cannot
consume produce an error identifying the instance, ports, expressions and compiler
diagnostic. Supply all referenced packages/dependencies. No child parameter or
localparam name is emitted in a generated top dimension after an override.

Whole unpacked value-array connections retain the child's packed type followed by
its concrete unpacked dimensions, e.g. `tlul_pkg::tl_h2d_t dev_h2d [2]`.
`dev_h2d[0]` selects one unpacked element and is checked against that element's
packed width. Element connections never widen or replace the whole-array net's
declaration. This also applies when element instances precede the whole-array
instance in the map. Unpacked array slices are rejected explicitly.

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

Selections (`sig[7:4]`, `sig[3]`, `sig[$1*8 +: 8]`,
`sig[($1+1)*8-1 -: 8]`) are explicit connections. After template substitution,
constant integer arithmetic determines the selected interval, parent bus size,
connection width and driver overlap. Symbolic selections retain unknown widths;
negative indices and nonpositive indexed widths fail explicitly. Constants (`1'b0`, `'0`, `8'hFF`, `'1`)
are valid input tie-offs. `null` and `""` emit `.port()`: outputs report unused;
inputs warn as undriven and should instead receive a constant when tied off.
Generated empty connections are individually enclosed in Verilator
`lint_off PINCONNECTEMPTY` / `lint_on PINCONNECTEMPTY` comments. These comments
acknowledge the explicit mapping without suppressing the soc-integrate checks.
Constants on outputs/inouts are errors. No automatic truncation/extension or
implicit slicing is performed.

Inout pads never auto-share. Bus-like ports (`tl_*`, `*_req`/`*_rsp` including
`_i`/`_o` suffixes, names containing `h2d`/`d2h`, `axi_`/`apb_`/`ahb_` prefixes)
and package/user/struct value types are also excluded from automatic sharing.
They receive separate instance/module-prefixed nets, with `auto-share-blocked`
messages when same-name candidates exist. To opt in, map each endpoint explicitly
to the same signal, e.g. `{"mappings":{"u_a.tl_i":"host","u_b.tl_i":"host"}}`.
Sharing multiple typed/bus inputs this way produces `explicit-bus-share` so the
protocol intent stays visible. Scalar clock/reset inputs retain auto-sharing.
Native interface/modport connections retain their existing interface rules.

Other unmapped same-name inputs share an external input only when their normalized
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
output storage redeclarations, header/body parameters, parameters with unpacked dimensions, header package imports,
and body localparams.
Extraction preserves symbolic widths and defaults. Generated concrete dimensions
simplify constant integer arithmetic (`[WIDTH-1:0]` with WIDTH=8 becomes `[7:0]`);
symbolic dimensions remain symbolic. Wrappers forward public parameters;
localparams never become instance overrides. Package/user-defined type text is
preserved verbatim in declarations; package-qualified or `_t` value types may
omit the input direction. Provide package/typedef sources to the HDL
tool. Unknown type widths produce a check warning rather than a guessed width.

Native interface ports support `bus_if.mp s`, `bus_if s`, generic `interface s` /
`interface.mp s`, and unpacked arrays such as `bus_if.mp s [N]` or `[0:N-1]`.
Parameterized types belong on the interface instance: `bus_if #(.W(32)).mp s`
is not legal port syntax and is rejected. Interface definitions can have parameter
and signal headers, e.g. `interface bus_if #(parameter int W=8)(input logic clk)`.
Pass definition files alongside module files (interface-only files are dependencies,
not managed child modules), through includes, or in `packages`. Extract reports the
definitions under `interfaces`; instantiate connects complete expressions.

Configure concrete instances by the mapped signal's base name:

```json
{
  "mappings": {"u_source.s": "bus", "u_sink.s": "bus"},
  "interfaces": {
    "bus": {
      "type": "bus_if",
      "parameters": {"W": 32},
      "ports": {"clk": "clk"},
      "unpacked": "[0:1]"
    }
  }
}
```

This emits `bus_if #(.W(32)) bus [0:1] (.clk(clk));`. Omit `unpacked` for a scalar;
whole-array ports infer their resolved dimensions. `type` is inferred from typed
ports; generic ports need a concrete peer on the same net or an explicit `type`.
Omitted parameter overrides use definition defaults. Interface header signals
default to same-name top signals; `ports` remaps them or supplies constants.
Parameter overrides also resolve dimensions of these signals. Definitions absent
from the input still permit typed instances with explicit `ports`/`parameters`.
Interface inputs using expressions beyond a simple identifier or constant need
an existing declaration. There is no protocol or per-signal modport-direction signoff. Integration, check
and update warn about interface-array elements with no connected child port
(`interface-element-unconnected`), or no connected output/inout modport
(`interface-element-undriven`). Whole-array ports cover all elements; `[N]`,
ascending and descending constant bounds are supported. Plain/generic interface
ports have unknown driver roles and do not establish an undriven finding. Opaque
user logic is not analyzed for interface drivers; review these warnings when
custom code drives an element. This is an element-coverage heuristic, not a check
that every individual signal inside a connected interface is driven.

For per-element connections, use scalar child ports and templates such as
`{"regex":"u_sink(\\d+)\\.s","value":"bus[$1]"}`. Constant indices infer a
zero-based interface instance array; explicit `unpacked` can specify its bounds.
Array child ports connect to the whole array. Update reads actual interface
parameter overrides, dimensions and header connections, and extract-map retains
these under `interfaces`. Definition source paths remain available for JSON-free
refresh. Verilator 5.032 rejects legal generic interface ports with `UNSUPPORTED`;
parser/generator/refresh tests still cover them, and generic lint tests explicitly
skip only when that compiler capability is absent. Concrete/modport ports and
arrays are linted with fatal warnings.

Inline aggregates, default-valued ports, positional/wildcard module connections
and module instance arrays/multiple instances per statement remain unsupported.
The parser is not a complete SystemVerilog elaborator. With package sources it
asks Verilator to elaborate an isolated public header using `--json-only` on
versions 5.032 and later (detected with `--version`). Compiler-folded `$bits`
localparam probes resolve typedef/packed struct/union sizes, and bound probes
resolve package constants in dimensions. These avoid incomplete pre-width JSON
dtype links. Older/unknown versions use legacy `--xml-only`. Unsupported JSON
options or AST schemas fall back to XML; unsupported XML options/schemas fall
back to the text parser's symbolic widths (`width-unknown` checks). If the isolated
header fails because declarations or constants need the module body, the tool retries the full real module, using disposable preprocessed source
with compiler probes. Full elaboration reads the AST's port names/directions and
folded bit/bound probes, while retaining the original type spelling; module-local
types use a concrete packed representation in parent declarations. Dependencies
come from repeatable `-y DIR` / `--library-dir DIR` (MCP `library_dirs`), the
module's sibling directory and remaining supplied source files passed as `-v`
libraries. Include directories, defines and packages are also forwarded. Full
elaboration uses `--top-module <module>` and `-Wno-fatal` for extraction only;
HDL errors fail with the module name and the first real Verilator error lines.
Original source locations, including included port declarations, accompany compiler diagnostics.
Original type spelling remains in metadata. Unqualified imported port types receive
package-qualified declarations in the parent; with multiple wildcard imports,
all supplied imported packages are searched for the typedef. Ambiguities identify
the module port and candidate package names. Explicit imports
retain precedence over wildcard imports. Extraction reports default-configuration
counts; integration re-evaluates overridden instances independently.
Supply all transitive package dependencies. `--package` / MCP `packages` accepts
any order: package declarations, imports and `pkg::name` references determine a
stable topological order, also used in generated lint filelists. Dependency
analysis uses active preprocessed text, ignoring comments/strings/inactive
branches. Missing packages and dependency cycles fail with real source file:line.
Files containing mutually interleaved package dependencies must be split if no
file order can satisfy them. This orders supplied files; use sibling
`soc-build.soc_flist` for project dependency discovery.
Without packages, named types remain symbolic and produce `width-unknown` checks.
Inline structs/aggregates, type parameters and default port values remain outside
the text parser's scope. Unsupported port declarations report a file, line and construct rather than dropping ports.

All RTL-reading MCP tools accept `include_dirs`, `defines`, `packages` and `library_dirs`.
CLI equivalents are repeated `-I dir`, `-D NAME[=value]`, `--package file.sv`
(in any order), repeatable `-y dir`, plus `+incdir+dir+dir` / `+define+NAME=value+NAME`.
When Verilator is on PATH, extraction uses `verilator -E --relative-includes`
over all package and source files together, with those options. A preprocessing
pass establishes package dependencies before the ordered extraction pass.
Cross-file macro definitions persist in the ordered compilation unit; macros
that require a particular source-file order still need that order.
Root and include `line directives split the output back by source file. Retained `line directives map each port
and diagnostic to the original source file and absolute line, including includes.
Function-like macros in headers and bodies are handled by Verilator.

Without Verilator the built-in preprocessor supports includes, object macros,
nested conditionals and undef. Function-like defines and body calls are skipped;
a function-like macro in a port/parameter header fails with a source location and
an instruction to install Verilator. Missing includes, undefined object macros,
recursive expansion and malformed conditionals fail explicitly. The fallback
cannot resolve package typedef widths or elaborate function-like header macros.

```bash
python3 scripts/soc_integrate.py extract peripheral.sv -I rtl/prim \
  --package rtl/common_pkg.sv --package rtl/peripheral_reg_pkg.sv -D FEATURE=1
```

## Scoped vendor lint

`integrate` / `update` / `remove` accept `--lint-config` (MCP `lint_config=True`).
This independently opts into `<output-stem>.vlt` and `<output-stem>.lint.f` next
to the output top. Pass `-y dir` / `--library-dir dir` (MCP `library_dirs`) for
library discovery. `--vendor-dir dir` (MCP `vendor_dirs`) explicitly opts a
directory into lint waivers without adding library discovery. Include directories
alone do not opt first-party RTL into waivers. Ordered `packages`, include directories, defines, interface
sources, library directories, module files and the top are included in the filelist.

```bash
python3 scripts/soc_integrate.py integrate vendor/ip.sv -n top -o top.sv \
  --package vendor/pkg.sv -I vendor/include -y vendor/rtl --lint-config
verilator --lint-only -Wall --top-module top top.vlt -f top.lint.f
```

The config starts with `` `verilator_config `` and scopes `lint_off -file` to
absolute sources under a `vendor/` path component and explicit library/vendor
directory globs. First-party module/package files outside those scopes keep
their warnings fatal, even when passed explicitly or through an include directory. It also
scopes `UNOPTFLAT` (performance) and `SYMRSVDWORD` (C++ symbol portability)
explicitly, since those diagnostics are outside Verilator's default lint group ([control-file syntax](https://verilator.org/guide/latest/control.html)).
The generated top never receives a waiver, including when it is within an
explicit vendor/library directory: those directories are enumerated with the top excluded.
Warnings introduced in the generated top still fail `-Wall`; `-Wno-fatal` is not
needed. Syntax/elaboration errors remain errors. Review the dependency scopes
before using this option on mixed first-party/vendor trees. Paths are absolute;
regenerate collateral when moving the checkout or changing dependencies.

## Filelists and integration boundaries

`integrate -f filelist` accepts source lines, `+incdir+`, `+define+`, `-I`, `-D`,
`-y`, comments (`#` and `//`) and nested `-f` lists. Paths resolve against each
filelist's directory. `update`/`remove`/top `check`/top `diff` also accept `-f`
for current module sources. Snapshot keeps its legacy `-f` format option.
Module selection `-m` is supported for module commands and validates the top
name on top check/diff. It is not accepted on integrate/update/remove/extract-map.

Consume sibling `soc-build.soc_flist` output as source/filelist input; this tool
does not replace project dependency discovery. Address-map inputs come from
`gen-asic-memmap`; register RTL and maps from `yml2reg`; clock/reset modules from approved `crg-gen` workbooks. This skill only wires
supplied modules. It does not generate reset synchronizers, reset-source logic,
address decoders/crossbars, project dependency filelists or testbenches. Route those
to `crg-gen`, `gen-asic-memmap`, `soc-build` and verification respectively. Existing
opt-in `.lint.f` is only a manifest of explicitly supplied inputs for the tool's
scoped lint config; it does not discover or create a project filelist. DFT readiness and SGDC remain
with `dft-gen` and the DFT owner per rule 14. These parser/refresh tools
do not infer or generate address maps, CRG trees, reset policy or DFT circuitry.

## MCP parameter reference

The following ordered parameter names exactly match the registered tool schemas.
Defaults/types are supplied by MCP; optional additions retain legacy call order.

```text
soc_extract(verilog_file, module_name, include_dirs, defines, packages, library_dirs)
soc_instantiate(verilog_file, instance_name, module_name, include_dirs, defines, packages, library_dirs)
soc_wrap(verilog_file, module_name, wrapper_name, output, include_dirs, defines, packages, library_dirs)
soc_csv(verilog_file, module_name, output, include_dirs, defines, packages, library_dirs)
soc_integrate(module_files, top_name, output_file, port_map, csv, track, strict, include_dirs, defines, packages, lint_config, library_dirs, vendor_dirs, force)
soc_update(config_file, output, port_map, top_name, module_files, top_file, csv, track, strict, include_dirs, defines, packages, lint_config, library_dirs, vendor_dirs)
soc_extract_map(top_file, output, verify_modules, expand, include_dirs, defines, packages, library_dirs)
soc_check(verilog_file, spec_file, module_name, module_files, strict, include_dirs, defines, packages, library_dirs)
soc_snapshot(verilog_file, module_name, output, format_type, version, changelog, include_dirs, defines, packages, library_dirs)
soc_diff(verilog_file, snapshot_file, module_name, module_files, include_dirs, defines, packages, strict, library_dirs)
soc_remove(config_file, module_name, module_files, include_dirs, defines, packages, lint_config, library_dirs, output, strict, port_map, vendor_dirs)
```
