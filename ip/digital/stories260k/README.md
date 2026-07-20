# stories260k IP

`stories260k` 是一个混合 W4/W8 推理引擎，在片上完整运行 llama2.c TinyStories
`stories260K` 开源 nano 模型（260,032 参数，8 查询头 / 4 KV 头 GQA）的贪心
自回归解码：token 嵌入、5 层 transformer（含 KV cache 追加）、final
RMSNorm、权重共享 logits 与融合 streaming argmax。全部权重、512 位置上下文、
激活与查找表都在片上 284 KiB SRAM（0.277 MB）内，运行时无外部访存。

背景故事：本 IP 是 Kimi K3 的早期概念验证——K3 在连续 48 小时自主运行中，
基于开源 EDA（OpenROAD 流程）与 Nangate 45nm 开放 PDK，独立完成了这颗
"由模型设计、为模型服务"的芯片的构建、优化与验证。过程并非一帆风顺：真实
检查点下载受阻（改由 hf-mirror 正确子目录路径解决）、初版输出退化为词汇
碎片，K3 自主完成定点调试（RMSNorm 除法 32 迭代精确商、MAC group fold 负数
floor 偏置改半进位舍入、scale 区陈旧常量、sq8 符号化、WBUF 交织布局等），
早期基线曾打印出与浮点模型一致的开篇 **"Once upon a"**。

v1.2 把串行 SCORE/SOFTMAX/AV 改成 8-position tile 融合 attention，并把敏感的
layer-1 WQ 提升为 INT8（复用原 WBUF 空闲 2 KiB，SRAM 容量不变）。真实镜像 VCS
实测 64/256/512 token 分别为 **12,810.6 / 10,815.5 / 8,955.8 token/s
@100 MHz**，最大上下文也达到 ≥8,700 指标。首 64 token 与修正后的定点黄金模型
逐 token 一致，开篇六个生成片段与 FP32 相同：`Once upon a time, there`；后续仍有
量化造成的碎词，属于 W4A8 与 FP32 的精度差距，不再是 RTL/黄金模型计算不一致。

## 模型与量化参数

顶层模块为 `stories260k`，单时钟、低有效异步复位、Verilog-2005。

| 参数 | 值 | 说明 |
|---|---:|---|
| DIM / HID / NLAYERS | 64 / 172 / 5 | llama2.c stories260K 几何 |
| q 头 / KV 头 / HEAD_DIM | 8 / 4 / 8 | GQA kv_mul=2，kv_dim=32；q 头 h 读 KV 头 h>>1 |
| VLEN / 检查点 seq / 芯片上下文上限 | 512 / 512 / 512 | 覆盖检查点声明的完整序列长度 |
| 参数总量 | 260,032 | emb 32,768 + 各层 45,440×5 + gains 704（分类器与 emb 共享） |
| 权重 | 除 layer-1 WQ 为 INT8 外均为 INT4；8×8 tile + 每 64 元素 scale | MAC 内融合反量化；WQ1 上下 4 行双读，不增加计算拍 |
| 激活 / 累加 | INT8 / INT32 | 残差全程 ×8 定点网格；每级写回饱和到 INT8 |
| KV cache | INT4 + 每 (layer,kv-head,pos) 2 的幂 scale(Q4.12) | K scale 折进 softmax 输入，V scale 折进 p' |
| MAC 阵列 | 8×8 = 64 MAC/cycle | 100 MHz 下 6.4 GMAC/s |

## SRAM 预算（总计 284 KiB = 290,816 B = 0.277 MB）

| Buffer | 容量 | 用量 | 字宽 | 内容 |
|---|---:|---:|---|---|
| WBUF | 148 KiB | 150,208 B（4,694/4,736 字） | 32 B | 混合 W4/W8 权重 133,632 B + scales 8,384 B + RoPE 8,192 B；余 1,344 B |
| KVBUF | 124 KiB | 122,880 B（3,840/3,968 字） | 32 B | 每层 4 KV 头 × 512 pos 的 K/V 数据与 scales，层 stride 768 字 |
| ACTBUF | 4 KiB | 3,536 B 地址包络（442/512 字） | 8 B | X/XB/Q/KT/V/ATT/HB/HB2/HB3/Y；SCORE/PR 区保留但不再访问 |
| VECBUF | 8 KiB | 1,704 B（213/1,024 字） | 8 B | RMSNorm gains、requant 表 37 槽 |

## 接口

| 信号 | 方向 | 位宽 | 说明 |
|---|---|---:|---|
| `clk` | input | 1 | 工作时钟（10 ns 约束，100 MHz 目标） |
| `rst_n` | input | 1 | 低有效异步复位（不清 buffer 内容） |
| `mm_valid` | input | 1 | MMIO 请求有效 |
| `mm_write` | input | 1 | 写请求选择 |
| `mm_addr` | input | 20 | 本地 byte address（1 MiB aperture） |
| `mm_wdata` | input | 32 | 写数据 |
| `mm_wstrb` | input | 4 | byte write strobes（CSR 写忽略） |
| `mm_rdata` | output | 32 | 读数据（寄存器化，受理后下一拍有效） |
| `mm_ready` | output | 1 | 请求受理（组合输出；busy 时仅 buffer 访问挂起） |
| `mm_error` | output | 1 | 当前请求错误（与读数据同拍） |
| `irq` | output | 1 | `irq_en && (done \| error \| token_valid)` |

地址窗口：CSR `0x00000-0x00FFF`，WBUF `0x10000-0x34FFF`，KVBUF
`0x40000-0x5EFFF`，ACTBUF `0x60000-0x60FFF`，VECBUF `0x64000-0x65FFF`，
其余 `INVALID_ADDR`。`GEN_CFG[20:17]` 为 softmax z 域下移 `sm_shift`
（默认 2，经混合 W4/W8 定点黄金模型校准）。

## 目录结构

```text
ip/digital/stories260k/
├── docs/                  # architecture / design_spec / interface_spec / regmap / verification_plan
├── de/
│   ├── rtl/               # stories260k.v / _regs / _spm / _mac / _sfu / _attn / _core
│   ├── run/
│   └── syn/               # stories260k.sdc（10 ns 时钟约束，非收敛证据）
└── dv/
    ├── tb/                # T1/T2、64/256/512 token T3、定点黄金前缀、T4
    ├── tests/             # pack_stories260k.py（镜像打包）、fixed_point_model.py（RTL 语义级黄金模型）
    ├── sim/               # 仿真输出与镜像（不入库）
    └── cov/
```

## 构建与验证入口

- 主机流程：加载 WBUF（tile 权重+scales+512-position RoPE）→ VECBUF（gains/结构化
  requant 0..34）→ 写 `TOKEN_IN`(BOS)、`GEN_CFG`（gen_len、sm_shift）→
  `CTRL.start`（连同 irq_en/chain_en）→ 每 token 更新 `TOKEN_OUT` 与
  `token_valid`（`chain_en=1` 自动回喂至 `gen_len_m1+1` 个 token；合法配置最多
  生成 512 个 token，填满位置 0..511）→ done/irq → 读 PERF 计数器按
  `TOKEN_CNT × f_clk / CYCLE` 计算吞吐。
- 真实模型镜像：

  ```bash
  wget https://hf-mirror.com/karpathy/tinystories/resolve/main/stories260K.bin
  python3 dv/tests/pack_stories260k.py stories260K.bin dv/sim/img
  ```

  TB 经 soc_sim 注入 `USER_SIM_FLAGS="+WIMAGE=…/wbuf.hex +VIMAGE=…/vecbuf.hex"`
  以 `$readmemh` 加载（256b/64b 每行）；缺省回退 LFSR 伪随机权重（结构回归，
  拍数与真实镜像一致）。
- 定点黄金模型（float vs fixed token 轨迹对照、grid/sm_shift 校准）：

  ```bash
  python3 dv/tests/fixed_point_model.py stories260K.bin [steps]
  ```

- T3 打印实测 token/s、MAC 利用率与分状态拍数直方图，并断言 ≥ 8,700；
  断言与测试矩阵见 `docs/verification_plan.md`。
- Agent 执行 lint、编译、仿真（`soc_comp`/`soc_sim`/`soc_regress`）和综合时必须
  使用注册的 `soc-build` MCP 工具，并通过 `pipeline_state.json` 门控；本地不得
  直接调模拟器。模块级 make 入口（`Makefile`、`de/Makefile`）与 npu 一致，
  目标经 MCP 工具转发执行。
