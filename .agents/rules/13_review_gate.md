# Independent review gate

Run `soc-reviewer normal` once for `merge`, `strict` for `signoff`, or `quick`
for an explicit read-only audit. Do not dispatch it during routine `dev`.
Review is not a pipeline stage and never writes source, state, waivers, or EDA
artifacts.

The reviewer inspects the relevant diff, untracked files, router mode, state,
artifact digests, registered check evidence, invalidation, repository hygiene,
and only the design domains supported by supplied artifacts. When a workspace
is available, run `check_loop_state.py <workspace> --mode <depth>`; this does not
replace judgment.

When `soc-ai-kb` is registered, query project rules before narrower IP/company
or general guidance. Only substantive sources under
`soc/review/rule_library/` are authoritative `Project Rule` evidence. Other
sources are `Reference Evidence`; placeholders or conclusions depending on a
missing rule use `Need Human Confirmation`. Local code defects, failed checks,
and missing evidence remain reportable as `Local Evidence`. Never invent a rule
ID, source, version, scope, waiver, or signoff conclusion.

Outcomes are `pass`, `needs-fix`, `needs-validation`, or `blocked`. Issues use
severity `Blocker|Critical|Major|Minor|Info`, confidence 0-100, authority
`Project Rule|Reference Evidence|Local Evidence`, owner, evidence, risk, fix,
impact, and status `Open|Need Human Confirmation|Waiver Review|Deferred|Resolved by Evidence`.

`quick` returns only Review Summary, actionable Issue List, and Next Actions.
`normal/strict` add Key Risks, Waiver Review, and Delivery Checklist. Omit empty
quick fields; use `Not Available` for missing required delivery evidence.
Separate must-fix, owner-confirmation, deferrable, and optimization actions.
Never state that the design is signed off.
