# Review gate

Use this rule for independent review after a pipeline-governed change, before commit, or whenever a task claims simulation, synthesis, timing, physical-design, or integration success.

## Reviewer role

Use `soc-reviewer` for loop audit when named agent profiles are available. If named role agents are unavailable, use a generic subagent with canonical `.agents/agents/soc-reviewer.md` as the role contract.

`soc-reviewer` is an audit role. It does not write RTL, testbench, constraints, generated tops, `pipeline_state.json`, waivers, or OpenROAD collateral. It does not run simulator, synthesis, STA, or OpenROAD tools. It reports findings and required follow-up checks.

The reviewer is a first-pass design review, not a signoff authority. Its coverage may include RTL/lint, clock/reset, CDC/RDC, protocols/registers/address maps, integration, UPF/low power, DFT, SDC/timing, synthesis/QoR, LEC/Formality, Formal, verification/regression/coverage, X-prop/GLS, security/access control, waivers, reproducibility, and documentation. It reviews only domains supported by supplied artifacts and explicitly lists unreviewed domains.

## Knowledge-base evidence

When `soc-ai-kb` is registered, query active project-specific rules first, then IP/subsystem, company, and general rules. Findings cite the matched rule ID, source, version, and scope. If the service is unavailable or no applicable rule is found, record that limitation and use `Need Human Confirmation` for conclusions that depend on the missing rule. Never fabricate a rule or convert generic model knowledge into a project requirement. Direct code defects, failed checks, missing evidence, and repository process violations remain reportable from local evidence.

## Review depth

Use the narrowest review mode that matches the risk:

- `quick`: inspect `git status`, relevant diffs, and pipeline-state shape. Use for planning and dry-run checks.
- `normal`: also validate artifact paths, stage checks, and basic PASS evidence. Use after stage work.
- `strict`: also check transient/generated files and commit-readiness risks. Use before commit or PR.

Run `.agents/scripts/check_loop_state.py <workspace> --mode <quick|normal|strict>` when a module workspace is in scope. This checker is read-only and does not replace reviewer judgment.

## Required checks

The reviewer checks:

- `git status --short`, tracked diff, and untracked files
- applicable `AGENTS.md` and `.agents/rules` requirements
- whether RTL/material changes triggered the correct gated flow
- whether `pipeline_state.json` status, artifacts, and check results match real files
- whether verification, synthesis, timing, and PD claims have real logs/reports
- whether downstream RTL repairs invalidated the opposite downstream stage when required
- whether generated/transient artifacts such as waveforms, simulator images, caches, and local logs are excluded from source changes
- whether EDA work used registered MCP tools rather than direct shell fallback

## Review outcomes

- `pass`: no blocking findings; residual risks are documented.
- `needs-fix`: findings require source, state, artifact, or documentation fixes before commit or downstream dispatch.
- `needs-validation`: implementation may be plausible, but a required registered MCP check or real evidence is missing.
- `blocked`: required files, tools, or decisions are unavailable.

A review result does not replace the module pipeline state machine. Do not add a `review` stage to `pipeline_state.json`; keep review findings in the final response, PR notes, or a dedicated reviewed artifact only when explicitly requested.

## Structured report contract

Reports contain, in order: `Review Summary`, `Key Risks`, `Issue List`, `Waiver Review`, `Delivery Checklist`, and `Next Actions`. Issues use severity `Blocker|Critical|Major|Minor|Info`, confidence 0-100, and proposed status `Open|Need Human Confirmation|Waiver Review|Deferred|Resolved by Evidence`. Every issue includes category, rule ID/source/version, file/line, associated report, evidence, risk, fix, impact, human-confirmation flag, owner, and proposed status. Missing fields are written as `Not Available`, not silently omitted.

`Next Actions` separates must-fix-before-merge items, owner confirmations, deferrable work, and optimizations. The report may recommend a registered MCP check but cannot execute EDA or claim design signoff.
