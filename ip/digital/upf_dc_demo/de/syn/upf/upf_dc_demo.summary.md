# upf_dc_demo Power Intent Diagram Summary

- input mode: power_intent
- supplies: 12 rows
- domains: 5 rows
- power states: 9 rows
- hard macros: 4 rows
- macro PG bindings: 8 rows

## Switchable Domains
- PD_SW VDD_SW 1.2V
- PD_ACC VDD_ACC 1.2V
- PD_PERI VDD_PERI 1.2V
- PD_MEDIA VDD_MEDIA 1.2V

## Derived UPF Intent / 推导出的 UPF
- supply_ports: 9 rows
- supply_nets: 13 rows
- supply_net_connections: 9 rows
- supply_sets: 12 rows
- domain_supplies: 3 rows
- power_domains: 5 rows
- power_switches: 4 rows
- hard_macros: 4 rows
- macro_pg: 8 rows
- port_attributes: 9 rows
- isolation: 4 rows
- level_shifters: 8 rows
- cell_maps: 8 rows
- power_states: 33 rows

## Auto-derived / 自动推导说明
- Supplies 表未定义地网络，默认使用 VSS (ground net defaulted to VSS).
- 单元映射按 Isolation_LS 库单元列或兼容 CellMaps 表生成，需与目标工艺库核对 (verify cell mappings against target libraries).
