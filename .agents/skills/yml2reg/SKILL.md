---
name: yml2reg
description: Generate APB/AHB/DAB regfile RTL, Spirit XML, Excel, C/sysmap headers, UVM regmodel/ral_lib/init/define, bus adapters, JSON/CSV regmap, and multi-block top RAL from YAML.
---

# YAML Register Map (yml2reg)

One approved YAML → RTL + software + verification pack. Outputs beside YAML by default (`output_dir` optional).

## Tools

| Tool | Output |
|------|--------|
| `yml2reg` | APB/AHB/DAB regfile RTL + interrupt banks |
| `yml2xml` | Spirit/IP-XACT XML |
| `yml2excel` | Excel table |
| `yml2reg_c` | C header with **sparse MMIO struct** (`reserved_*` holes) |
| `yml2sysmap` | module sysmap fragment |
| `yml2uvm_ral` | UVM regmodel `NAME_ral.svh` |
| `yml2uvm_ral_top` | multi-block top RAL from `type: top` YAML |
| `yml2sv_define` | `*_regs_define.h` / `.svh` |
| `yml2regs_init` | `*_regs_init.sv` / `.c` / `.h` |
| `yml2ral_lib` | `*_regs_ral_lib.svh` (extends block + config) |
| `yml2bus_adapters` | `yml2reg_bus_adapters.svh` (APB/AHB/DAB templates) |
| `yml2regmap_export` | `*_regmap.json` + `*.csv` |
| `yml2docs` | one-shot full pack (no RTL) |

## Full pack (recommended)

```text
yml2docs(yaml_file=..., targets="xml,excel,h,sysmap,ral,define,init,ral_lib,regmap,adapter")
yml2reg(yaml_file=..., protocol="apb")
```

Top multi-block:

```text
yml2docs(yaml_file=demo_top.yml)   # auto-detects blocks:[]
# or
yml2uvm_ral_top(yaml_file=demo_top.yml, emit_children=true)
```

## YAML extras (DV)

```yaml
coverage: true                 # UVM_CVR_ALL in RAL
hdl_path: u_sys_ctrl           # block HDL root
hdl_path_prefix: tb.dut        # => tb.dut.u_sys_ctrl
fields:
  - {name: enable, ..., hdl_path: custom_slice_name}  # optional
```

Top YAML (`references/demo_top.yml`):

```yaml
name: DEMO_CHIP_TOP
type: top
blocks:
  - yaml: demo_docs.yml
    base_address: 0x1000
    instance: u_sys_ctrl
    hdl_path: tb.dut.u_sys_ctrl
```

## Interrupt banks

Expand to RAW/STAT/MASK/SET/CLR/MODE/POLAR (RTL + RAL + headers), rals_parser aligned.

## Notes

- C header struct now inserts `volatile uint32_t reserved_*[]` for offset holes — safe for MMIO cast when offsets are word-aligned.
- Bus adapters are templates; replace `apb_seq_item` / `ahb_seq_item` / `dab_seq_item` with project types if needed.
- Do not hand-edit generated files; change YAML and regenerate.
