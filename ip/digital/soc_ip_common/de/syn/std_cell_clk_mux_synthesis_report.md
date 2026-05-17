# Synthesis Report: std_cell_clk_mux

## 1. Overview

| Item | Value |
|------|-------|
| Module | std_cell_clk_mux |
| Function | Glitch-free 2-to-1 clock multiplexer with active-high enable |
| Tool | Yosys 0.9 (git sha1 UNKNOWN, clang 11.0.3) |
| SDC | de/syn/std_cell_clk_mux.sdc |
| Date | 2026-05-17 |

## 2. Synthesis Command

```bash
cd /Users/ninghechuan/vibe_soc/ip/digital/soc_ip_common && \
make syn RTL_TOP=std_cell_clk_mux
```

Generated Yosys script (`de/syn/syn.ys`):
```
read_verilog <rtl_files>
hierarchy -check -top std_cell_clk_mux
proc; flatten; opt; fsm; opt; memory; opt; techmap; opt
write_verilog std_cell_clk_mux_netlist.v
stat
```

## 3. Netlist Statistics

### 3.1 Cell Count (from Yosys `stat`)

| Cell Type | Count | Description |
|-----------|-------|-------------|
| `$_AND_` | 4 | 2-input AND gates |
| `$_DLATCH_P_` | 2 | Positive-enable transparent latches |
| `$_NOT_` | 3 | Inverters |
| `$_OR_` | 1 | 2-input OR gate |
| **Total cells** | **10** | |

### 3.2 Wire Count

| Metric | Value |
|--------|-------|
| Number of wires | 14 |
| Number of wire bits | 14 |
| Number of public wires | 11 |
| Number of public wire bits | 11 |

### 3.3 Sequential Elements

| Type | Count | Status |
|------|-------|--------|
| Latches | 2 | **INTENTIONAL** - core of glitch-free clock mux |
| Flip-flops | 0 | |
| Memories | 0 | |

### 3.4 Latch Detail

| Latch | Domain | Function |
|-------|--------|----------|
| `en0_latch` | clk0 | Captures sel0 state during clk0 low phase |
| `en1_latch` | clk1 | Captures sel1 state during clk1 low phase |

Both latches are **intentionally inferred** from the `always @(*)` blocks with
`if (!clk)` conditions. This is the standard glitch-free clock mux architecture.

## 4. Timing Analysis

**WNS/TNS: N/A**

This is a latch-based clock multiplexer with no flip-flops. There are no
traditional sequential timing paths (setup/hold) to analyze. The design relies on:

- Latch transparency during clock low phases to safely propagate select signals
- AND-OR combinational logic for final clock gating
- Clock sources are declared as logically exclusive (no cross-clock paths)

Timing verification should be performed at the SoC integration level with:
- Proper latch transparency window analysis
- Clock skew constraints between clk0/clk1 and their respective latches
- Glitch-free transition verification via simulation

## 5. Warnings / Notes

### 5.1 Expected Messages

Yosys correctly inferred 2 latches:
```
Latch inferred for signal `\std_cell_clk_mux.\en1_latch'
Latch inferred for signal `\std_cell_clk_mux.\en0_latch'
```

These are **expected and correct** for this design.

### 5.2 No Errors

- No synthesis errors
- No unintended latches (exactly 2, both intentional)
- No flip-flops inferred
- No FSMs detected
- No memories inferred

## 6. Design Equivalence

The synthesized netlist preserves the original RTL structure:

```
RTL Structure                    Netlist Mapping
---------------                  ---------------
sel0 = ~sel & clk_en      -->   $_NOT_ + $_AND_
sel1 = sel & clk_en       -->   $_AND_
en0_latch (latched by ~clk0) --> $_DLATCH_P_ (E=~clk0)
en1_latch (latched by ~clk1) --> $_DLATCH_P_ (E=~clk1)
gated_clk0 = clk0 & en0   -->   $_AND_
gated_clk1 = clk1 & en1   -->   $_AND_
clk_out = gated0 | gated1 -->   $_OR_
```

The 3 inverters (`$_NOT_`) account for:
- 1x inversion of `sel` for `sel0`
- 1x inversion of `clk0` for latch enable (E=~clk0)
- 1x inversion of `clk1` for latch enable (E=~clk1)

## 7. Area Estimate

| Cell Type | Count | GE/cell | Subtotal |
|-----------|-------|---------|----------|
| NOT | 3 | 0.5 | 1.5 GE |
| AND | 4 | 1.0 | 4.0 GE |
| OR | 1 | 1.0 | 1.0 GE |
| DLATCH | 2 | 3.0 | 6.0 GE |
| **Total** | **10** | | **~12.5 GE** |

## 8. Recommendations

1. **Physical Implementation**: Ensure latch cells are placed close to their
   respective clock buffers to minimize clock-to-latch skew.

2. **DFT**: The `set_dont_touch` constraints in the SDC preserve the latch
   structure. Consider scan insertion strategy for clock mux cells.

3. **Clock Tree Synthesis**: The `set_clock_groups -logically_exclusive`
   declaration prevents false timing paths between clk0 and clk1 domains.

4. **Verification**: Confirm glitch-free behavior via gate-level simulation
   with async clock sources of different frequencies.
