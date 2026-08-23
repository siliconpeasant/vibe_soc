---
name: xml2yml
description: >
  Convert IP-XACT / Spirit XML register maps into yml2reg-compatible YAML
  (xml2yml / ipxact2yml). Use when the approved register source is Spirit XML,
  IP-XACT, or yml2xml output and you need YAML for RTL/DV/SW generation.
  Exclusive skill of soc-integrator — other roles must not call it.
---

# XML / IP-XACT → yml2reg YAML

**Owner role:** `soc-integrator` only. MCP `xml2yml` is connected at the
project parent for routing; execution remains exclusive to the integrator
through named MCP inheritance. After conversion, the same owner runs `yml2reg`
/ `yml2docs` for RTL and packs.

One Spirit/IP-XACT XML → yml2reg YAML. Then run `yml2reg` / `yml2docs` for RTL and packs.

## Tools

| Tool | Role |
|------|------|
| `xml2yml` | Primary converter |
| `ipxact2yml` | Alias of `xml2yml` |

## Args

- `xml_file` (required): Spirit / IP-XACT XML path
- `output_dir` (optional): default beside the XML
- `name` (optional): override YAML `name`
- `protocol` (optional): `apb` / `ahb` / `dab`
- `fold_interrupts` (optional): collapse expanded `*_raw`/`*_stat`/… banks into `interrupts[]`

## Supported XML shapes

1. **Project dialect** from `yml2reg` / `yml2xml`  
   `spirit:component` + `spirit:addressBlock` + `register` / `interrupt`  
   (namespace `http://www.siliconpeasant.com`, optional field `lockOffset` / `lockWidth` / `lockValue`).
2. **IEEE-style Spirit / IP-XACT**  
   `component` → `memoryMaps` → `memoryMap` → `addressBlock` → `register` → `field`  
   (`spirit:` or `ipxact:` prefixes; matching is by local-name).

Multiple `addressBlock`s → multiple YAML files.

## Recommended flow

```text
xml2yml(xml_file=.../regs.xml, output_dir=.../docs)
# review the generated YAML, then:
yml2docs(yaml_file=.../BLOCK.yml)
yml2reg(yaml_file=.../BLOCK.yml, protocol="apb")
```

CLI (no MCP):

```bash
python3 .agents/skills/xml2yml/scripts/xml2yml.py path/to/regs.xml -o out/
```

## Notes

- Output is yml2reg schema (`lsb`/`bits`/`access` lowercase, optional `interrupts`).
- Do not hand-edit generated YAML for long-lived sources; fix XML (or promote YAML to the approved source) and regenerate.
- Full IEEE vendor extensions / vendorExtensions are ignored unless mapped above.
- After conversion, treat YAML as the working register source for `yml2reg`.

## References

- `references/demo_spirit.xml` — project dialect (roundtrip with yml2xml)
- `references/demo_ipxact.xml` — minimal IEEE-style IP-XACT addressBlock tree
