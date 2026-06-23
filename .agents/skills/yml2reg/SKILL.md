---
name: yml2reg
description: Generate APB or AHB Verilog register-file RTL from a YAML register description. Use for deterministic register implementation from an approved YAML source.
---

# YAML to Register RTL

Call the registered `yml2reg` MCP tool with an existing YAML file and `protocol=apb|ahb`. Output is written beside the YAML input; failures are MCP tool errors.

Supported access types are `rw`, `ro`, `wo`, `w1t`, and `wc`.

Minimal YAML:

```yaml
name: my_reg
bytes: 4
offset: 0x000
registers:
  - name: ctrl_reg
    offset: 0x0
    fields:
      - {name: enable, lsb: 0, bits: 1, access: rw, reset: 0x0}
```

Review generated bus timing, reset values, address decode, and access semantics before integration. Do not hand-edit generated RTL; change the YAML and regenerate.
