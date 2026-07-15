# UPF/DC five-domain interface specification

## Top-level functional ports

The exact RTL top is `upf_dc_demo`. It has no parameters and no functional power/ground ports.

| Signal | Direction | Width | Description |
|---|---|---:|---|
| `clk` | input | 1 | 100 MHz AO/controller/macro clock |
| `rst_n` | input | 1 | Active-low asynchronous reset |
| `sw_clk` | input | 1 | 100 MHz `PD_SW` clock |
| `sw_power_req_i` | input | 1 | Requested `PD_SW` ON state |
| `sw_req_data_i` | input | 8 | `PD_SW` request data |
| `sw_req_valid_i` | input | 1 | `PD_SW` request qualifier |
| `sw_rsp_data_o` | output | 8 | Captured `PD_SW` response |
| `sw_rsp_valid_o` | output | 1 | Captured `PD_SW` response qualifier |
| `sw_powered_o` | output | 1 | `PD_SW` behavioral power observation |
| `sw_isolated_o` | output | 1 | High while `PD_SW` isolation is active |
| `acc_clk` | input | 1 | 100 MHz `PD_ACC` clock |
| `acc_power_req_i` | input | 1 | Requested `PD_ACC` ON state |
| `acc_req_data_i` | input | 8 | `PD_ACC` request data |
| `acc_req_valid_i` | input | 1 | `PD_ACC` request qualifier |
| `acc_rsp_data_o` | output | 8 | Captured `PD_ACC` response |
| `acc_rsp_valid_o` | output | 1 | Captured `PD_ACC` response qualifier |
| `acc_powered_o` | output | 1 | `PD_ACC` power observation |
| `acc_isolated_o` | output | 1 | High while `PD_ACC` isolation is active |
| `peri_clk` | input | 1 | 100 MHz `PD_PERI` clock |
| `peri_power_req_i` | input | 1 | Requested `PD_PERI` ON state |
| `peri_req_data_i` | input | 8 | `PD_PERI` request data |
| `peri_req_valid_i` | input | 1 | `PD_PERI` request qualifier |
| `peri_rsp_data_o` | output | 8 | Captured `PD_PERI` response |
| `peri_rsp_valid_o` | output | 1 | Captured `PD_PERI` response qualifier |
| `peri_powered_o` | output | 1 | `PD_PERI` power observation |
| `peri_isolated_o` | output | 1 | High while `PD_PERI` isolation is active |
| `media_clk` | input | 1 | 100 MHz `PD_MEDIA` clock |
| `media_power_req_i` | input | 1 | Requested `PD_MEDIA` ON state |
| `media_req_data_i` | input | 8 | `PD_MEDIA` request data |
| `media_req_valid_i` | input | 1 | `PD_MEDIA` request qualifier |
| `media_rsp_data_o` | output | 8 | Captured `PD_MEDIA` response |
| `media_rsp_valid_o` | output | 1 | Captured `PD_MEDIA` response qualifier |
| `media_powered_o` | output | 1 | `PD_MEDIA` power observation |
| `media_isolated_o` | output | 1 | High while `PD_MEDIA` isolation is active |
| `mem_cs_i` | input | 1 | AO SRAM access enable |
| `mem_we_i` | input | 1 | AO SRAM write select |
| `mem_addr_i` | input | 4 | AO SRAM word address |
| `mem_wdata_i` | input | 8 | AO SRAM write data |
| `mem_rdata_o` | output | 8 | AO SRAM read data |
| `mem_rvalid_o` | output | 1 | AO SRAM read qualifier |
| `pll_enable_i` | input | 1 | PLL teaching-model enable |
| `pll_clk_mon_o` | output | 1 | Observation-only modeled clock |
| `pll_locked_o` | output | 1 | Modeled PLL lock status |
| `pad_in_i` | input | 1 | External input-pad stimulus |
| `pad_in_core_o` | output | 1 | AO-side input-pad observation |
| `pad_out_core_i` | input | 1 | AO-side output-pad drive |
| `pad_out_o` | output | 1 | External output-pad observation |

## Child interfaces

Each of `u_aon_ctrl`, `u_acc_aon_ctrl`, `u_peri_aon_ctrl`, and `u_media_aon_ctrl` instantiates `upf_dc_demo_aon_ctrl` with `clk`, `rst_n`, one `sw_power_req_i`, 8-bit/valid core response, and outputs `sw_en_o`, `sw_iso_n_o`, `traffic_enable_o`, and 8-bit/valid captured response.

Each of `u_sw_core`, `u_acc_core`, `u_peri_core`, and `u_media_core` instantiates `upf_dc_demo_sw_core` with its dedicated `clk`, common `rst_n`, AO-generated `pwr_on_i`, 8-bit/valid request, and 8-bit/valid response.

PLL, SRAM, and pad child interfaces are unchanged from their RTL module declarations. Their functional interfaces contain no PG ports; synthesis-only PG pins come from Liberty and are connected by UPF.

## UPF and timing attributes

`sw_clk`, `acc_clk`, `peri_clk`, and `media_clk` receive driver supplies `SS_VDD_SW_VSS`, `SS_VDD_ACC_VSS`, `SS_VDD_PERI_VSS`, and `SS_VDD_MEDIA_VSS`, respectively. All other ordinary top digital ports are AO-relative except the preserved IO-pad attributes. The four external/core pad paths remain analog-exempt.

All five clocks have a 10.000 ns nominal period. Requests are accepted only after the corresponding AO controller has enabled power and released isolation. Reset and the ten request-side signals per domain cross from AO with the power shadow for eleven H2L shifted inputs total. Nine response bits per domain cross through output ELS protection. There are no cross-domain combinational paths between switchable domains.
