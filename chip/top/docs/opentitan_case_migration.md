# OpenTitan Case Migration

Source image directory: `/project/xuanwu9000/user/silicon/opentitan-master/scratch/codex_sw_image_build/earlgrey_all/20260627_092415_internal_ubuntu`

Case index files live under `chip/top/dv/tb/tests/`:

- `opentitan_cases.manifest.json`: index manifest consumed by `chip/top/Makefile`
- `opentitan_chip_sw_cases.json`: 185 migrated chip-level SW cases
- `opentitan_rom_e2e_cases.json`: 52 ROM E2E / ROM cases
- `opentitan_ate_cases.json`: 3 ATE bootstrap cases
- `opentitan_pure_dv_cases.json`: 34 indexed-only pure DV / CSR / Xbar cases
- `opentitan_case_overrides.yml`: small vibe_soc-local override layer

Total indexed cases: 274

Software case directories total: 188

The pure DV / CSR / Xbar entries are indexed for visibility only. They are not enabled as supported `chip/top` simulations until their build/run modes are validated in the vibe_soc flow.

No compile, simulation, or regression was run as part of the migration. Later dry-run Makefile expansion checks were used only to verify case-index lookup.
