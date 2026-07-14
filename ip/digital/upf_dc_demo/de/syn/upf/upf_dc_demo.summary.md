# upf_dc_demo Power Intent Diagram Summary

- input mode: power_intent
- supplies: 6 rows
- domains: 2 rows
- power states: 2 rows
- hard macros: 4 rows
- macro PG bindings: 8 rows

## Switchable Domains
- PD_SW VDD_SW 1.2V

## Derived UPF Intent / 推导出的 UPF
- supply_ports: 6 rows
- supply_nets: 7 rows
- supply_net_connections: 6 rows
- supply_sets: 6 rows
- domain_supplies: 3 rows
- power_domains: 2 rows
- power_switches: 1 rows
- hard_macros: 4 rows
- macro_pg: 8 rows
- port_attributes: 6 rows
- isolation: 1 rows
- level_shifters: 2 rows
- cell_maps: 2 rows
- power_states: 11 rows

## Auto-derived / 自动推导说明
- Supplies 表未定义地网络，默认使用 VSS (ground net defaulted to VSS).
- 单元映射按 Isolation_LS 库单元列或兼容 CellMaps 表生成，需与目标工艺库核对 (verify cell mappings against target libraries).
