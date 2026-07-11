# Design knowledge-base contract

All substantive development tasks must be evidence-led. When `soc-ai-kb` is registered, query it before architecture, documentation, RTL, verification, synthesis, physical-design, integration, lint-fix, or material-refactoring decisions. If it is unavailable, do not block a fresh clone solely for that reason; record the unavailable capability, local evidence used, and engineering assumptions.

The resulting artifacts must cite or summarize the knowledge-base evidence that influenced the design. If the knowledge base has insufficient evidence for a material design choice, state that explicitly and record the engineering assumption.

Apply this rule broadly:

- Architecture and design documents cite the relevant domain, methodology, interface, memory, datapath, control, low-power, DFT, safety, or process evidence.
- RTL implementations follow the approved documents and any relevant coding/tool guidance found in the knowledge base.
- Verification plans and testbenches use relevant verification methodology, scoreboard, coverage, assertion, and error-injection guidance.
- Lint, synthesis, timing, CDC/RDC, and physical-design fixes query the knowledge base using the rule name, diagnostic text, or failing concept before applying a material fix or waiver.
- Domain-specific designs, such as NPU, CRG, interconnect, register files, memories, or bus wrappers, query domain-specific knowledge before scope, interface, and microarchitecture decisions.

When RTL grows beyond a readable single file, split it into focused Verilog/SystemVerilog modules and update `de/rtl/filelist.f`. Prefer clear ownership boundaries such as frontend/registers, datapath, memory, controller/sequencer, protocol adapter, and arithmetic/helper units. Each module remains subject to the same `doc -> rtl -> {verif, syn}` pipeline and registered MCP checks.

Do not expand scope into new protocols, autonomous DMA, cache hierarchy, generated clocks/resets, safety mechanisms, DFT wrappers, SRAM macros, or physical-design assumptions unless the architecture and doc stages explicitly approve those choices with knowledge-base evidence or a documented lack of evidence.

For `soc-reviewer`, knowledge-base evidence is ordered by specificity: active project rules, IP/subsystem rules, company rules, then general rules. Each cited rule includes its ID, source, version, and scope. If no applicable rule is found, rule-dependent findings use `Need Human Confirmation`; the reviewer must not invent authoritative requirements.

For reviewer decisions, only knowledge-base sources under `soc/review/rule_library/` have project-rule authority. Other sources are reference evidence and cannot independently create a project violation, set `Blocker` or `Critical` severity, or justify a waiver. A project-rule file containing only a heading or no substantive requirement is a placeholder and requires `Need Human Confirmation`.
