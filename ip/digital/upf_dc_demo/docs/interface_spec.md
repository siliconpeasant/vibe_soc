# UPF/DC demo interface specification

## Top module

The exact functional RTL top is `upf_dc_demo`; it has no parameters and contains no power/ground ports. Top supply ports and macro PG pins are created by UPF and Liberty during synthesis and appear only in PG-aware synthesis outputs.

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | input | 1 | 100 MHz always-on reference clock |
| `sw_clk` | input | 1 | 100 MHz switchable-domain clock, externally driven at 1.2 V |
| `rst_n` | input | 1 | Active-low asynchronous reset; synchronous release |
| `sw_power_req_i` | input | 1 | Desired switchable-domain ON state |
| `req_data_i` | input | 8 | 1.8 V-side operand |
| `req_valid_i` | input | 1 | Operand qualifier |
| `rsp_data_o` | output | 8 | Always-on captured result |
| `rsp_valid_o` | output | 1 | Captured response qualifier |
| `sw_powered_o` | output | 1 | Observation of internal `sw_en` |
| `sw_isolated_o` | output | 1 | High while `sw_iso_n` is low |
| `mem_cs_i` | input | 1 | SRAM transaction enable |
| `mem_we_i` | input | 1 | SRAM write selection |
| `mem_addr_i` | input | 4 | SRAM word address |
| `mem_wdata_i` | input | 8 | SRAM write data |
| `mem_rdata_o` | output | 8 | SRAM registered read data |
| `mem_rvalid_o` | output | 1 | SRAM read qualifier |
| `pll_enable_i` | input | 1 | PLL teaching-model enable |
| `pll_clk_mon_o` | output | 1 | Observation-only modeled clock |
| `pll_locked_o` | output | 1 | Modeled lock status |
| `pad_in_i` | input | 1 | External 3.3 V-side pad stimulus |
| `pad_in_core_o` | output | 1 | 1.8 V core-side pad observation |
| `pad_out_core_i` | input | 1 | 1.8 V core-side pad drive |
| `pad_out_o` | output | 1 | External 3.3 V-side pad observation |
`VDD_AO`, `VDD_PLL`, `VDD_MEM`, `VDDIO`, `VDD_SW_IN`, `VDD_SW`, and `VSS` are UPF supply objects, not functional RTL ports.

## Child interfaces

### `upf_dc_demo_aon_ctrl u_aon_ctrl`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | input | 1 | Reference clock |
| `rst_n` | input | 1 | Active-low reset |
| `sw_power_req_i` | input | 1 | Desired power state |
| `core_rsp_data_i` | input | 8 | Protected switchable response |
| `core_rsp_valid_i` | input | 1 | Protected response qualifier |
| `sw_en_o` | output | 1 | Active-high abstract switch control |
| `sw_iso_n_o` | output | 1 | Active-high isolation release |
| `traffic_enable_o` | output | 1 | Request admission enable |
| `rsp_data_o` | output | 8 | Captured/clamped result |
| `rsp_valid_o` | output | 1 | Captured/clamped qualifier |

### `upf_dc_demo_sw_core u_sw_core`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | input | 1 | Switchable-domain clock driven by top `sw_clk` |
| `rst_n` | input | 1 | Active-low reset crossing from `PD_AO` |
| `pwr_on_i` | input | 1 | Behavioral availability shadow |
| `req_data_i` | input | 8 | Request operand |
| `req_valid_i` | input | 1 | Request qualifier |
| `rsp_data_o` | output | 8 | Registered operand plus one |
| `rsp_valid_o` | output | 1 | One-cycle qualifier |

### `upf_dc_demo_pll_macro u_pll_macro`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `ref_clk_i` | input | 1 | Reference clock |
| `rst_n` | input | 1 | Behavioral reset |
| `enable_i` | input | 1 | Behavioral enable |
| `pll_clk_o` | output | 1 | Observation-only modeled clock |
| `locked_o` | output | 1 | Lock status after four reference edges |

### `upf_dc_demo_sram_16x8 u_sram_macro`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | input | 1 | Synchronous port clock |
| `rst_n` | input | 1 | Behavioral reset |
| `cs_i` | input | 1 | Transaction enable |
| `we_i` | input | 1 | Write when high, read when low |
| `addr_i` | input | 4 | Word address 0 through 15 |
| `wdata_i` | input | 8 | Write data |
| `rdata_o` | output | 8 | Registered read data |
| `rvalid_o` | output | 1 | Read response qualifier |

### `upf_dc_demo_pad_in u_pad_in`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `pad_i` | input | 1 | External 3.3 V-side digital input |
| `core_o` | output | 1 | Core-side digital output |

### `upf_dc_demo_pad_out u_pad_out`

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `core_i` | input | 1 | Core-side digital drive |
| `pad_o` | output | 1 | External 3.3 V-side output |

## UPF attributes, timing, and protocol

Always-on digital inputs/outputs use `SS_VDD_AO_VSS` as their driver/receiver supply except the external pad sides, which use `SS_VDDIO_VSS`. At macro boundaries, driver/receiver attributes document `u_pad_in/core_o` as a 3.3 V-relative source into a 1.8 V receiver and `u_pad_out/core_i` as a 3.3 V-relative receiver driven by a 1.8 V source. Those four point-to-point pad boundary ports are also marked analog so Power Compiler does not insert core standard-cell LS/repeaters where a real characterized IO macro must own the conversion. This creates no additional domain or pad core PG pins. `sw_clk` is attributed to `SS_VDD_SW_VSS` and enters `PD_SW` directly.

Always-on logic and macros use rising `clk`; `u_sw_core` uses rising `sw_clk`. Both nominal periods are 10.000 ns. `pll_clk_mon_o` has no sequential endpoint. Hold reset low through both clock domains and release synchronously in this bounded teaching setup. Requests are accepted only after power is enabled and isolation released. Power-down asserts isolation before removing power. SRAM and pad interfaces are direct point-to-point connections, not buses.

UPF must use `extra_supplies_1/2/3` and hierarchical `connect_supply_net` for all synthesis-only Liberty PG pins. Reference evidence: *Power Compiler User Guide*, U-2022.12-SP3, pp. 227, 268, 258, and 259 respectively for multiple supplies, numbered additional supplies, hierarchical PG connectivity, and PG-netlist emission from UPF.
