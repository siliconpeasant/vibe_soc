# wave-mcp 波形调试

[Tencent wave-mcp](https://github.com/Tencent/wave-mcp) 是腾讯蓬莱实验室验证团队开源的 RTL 波形调试 MCP Server，支持读取 FST 与 RTL 网表、查询信号、追踪驱动和值/X 态，以及对比 pass/fail 波形的首个分歧。使用 Python 3.10–3.13；本仓库固定安装 [PyPI `wave-mcp==1.1.1`](https://pypi.org/project/wave-mcp/1.1.1/)，许可证为 Apache-2.0。

## 安装

推荐安装到用户独立虚拟环境：

```bash
python3 -m venv ~/.venvs/wave-mcp
~/.venvs/wave-mcp/bin/pip install 'wave-mcp==1.1.1'
```

也可以在仓库根目录安装，`.wave-mcp-venv/` 已加入忽略规则：

```bash
python3 -m venv .wave-mcp-venv
.wave-mcp-venv/bin/pip install 'wave-mcp==1.1.1'
```

`scripts/mcp_wave_mcp.sh` 按以下顺序查找可执行文件：

1. 环境变量 `WAVE_MCP_BIN` 指定的可执行文件。
2. 仓库内 `.wave-mcp-venv/bin/wave-mcp`。
3. `$HOME/.venvs/wave-mcp/bin/wave-mcp`。

没有找到时，launcher 在 stderr 打印固定版本的安装命令并退出。启动前清除 `PYTHONHOME`、`PYTHONPATH`，以 `--transport stdio` 启动外部二进制，并透传额外参数，例如：

```bash
scripts/mcp_wave_mcp.sh --session tmp/wave-mcp/tb_top
```

该运行时独立安装，与 `openroad-mcp` 一样使用 manifest 的 `command` 入口；`make agent-setup` 不负责安装 wave-mcp。

## 启用 MCP

在 `.agents/mcp-servers.json` 中将 `wave-mcp` 条目的 `default_enabled` 改为 `true`，然后在仓库根目录运行：

```bash
make agent-setup
```

这会从 canonical manifest 同步客户端配置和运行时入口。只需重新生成 Codex 与通用 MCP 配置时，可运行：

```bash
python3 scripts/sync_mcp_configs.py --write
python3 scripts/sync_mcp_configs.py --check
```

不要手改 `.codex/config.toml` 或 `.mcp.json`。`default_enabled` 控制生成的 Codex/Grok 启用状态；通用 `.mcp.json` 只列出服务，是否启用由客户端管理。重新加载客户端后即可使用 MCP 工具。

## Verilator 生成 FST

Verilator 构建需包含 `--binary --trace-fst`（带延时的 TB 通常还需 `--timing`），TB 中启用 dump，例如顶层名为 `tb_top`：

```systemverilog
initial begin
    $dumpfile("dump.fst");
    $dumpvars(0, tb_top);
end
```

对应的 Verilator 参数示意为 `verilator --binary --timing --trace-fst --top-module tb_top -f rtl.f`；运行生成的仿真程序后，FST 写到其工作目录下的 `dump.fst`。仓库内 EDA 构建与仿真仍通过注册的 `soc-build` 工具执行：在其构建配置中加入上述选项，并使用 `soc-build.soc_sim` 生成真实波形。

## 建立 session 与查询

以下命令从仓库根目录执行；先将实际仿真的 FST、顶层和 filelist 路径替换到示例中。filelist 应与仿真使用的 RTL 源码一致，包含所需的 include 路径、宏和 package。先把所选虚拟环境的 `bin` 加到 PATH（仓库内安装时改为 `.wave-mcp-venv/bin`）：

```bash
export PATH="$HOME/.venvs/wave-mcp/bin:$PATH"
mkdir -p tmp/wave-mcp
wave-session --fst ip/digital/example/dv/sim/dump.fst \
  --top tb_top --filelist ip/digital/example/de/run/rtl.f \
  --out tmp/wave-mcp/tb_top

wave-mcp query list_signals --session tmp/wave-mcp/tb_top --path tb_top
wave-mcp query signal_values --session tmp/wave-mcp/tb_top --paths tb_top.dut.done
wave-mcp query signal_drivers --session tmp/wave-mcp/tb_top --path tb_top.dut.done
```

`list_signals` 查询实例信号；`signal_values` 读取变化值；`signal_drivers` 查询 RTL 驱动位置。1.1.1 的参数名分别为 `--path`、`--paths`、`--path`；可用 `wave-mcp query <工具名> --help` 查看详情，或加 `--json` 输出结构化结果。MCP 模式也可调用 `prepare_session` 建立会话，再使用 `trace_value`、`trace_x` 追踪异常，或 `diff_waveforms` 比较同一设计的 pass/fail 波形。session 和波形留在被忽略的工作目录中，不提交到仓库。
