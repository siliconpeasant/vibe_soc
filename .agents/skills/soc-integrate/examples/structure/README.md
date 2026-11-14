# Package/CLI compatibility example

From the skill directory:

```bash
python3 scripts/soc_integrate.py extract examples/structure/leaf.sv
PYTHONPATH=scripts python3 -c "from soc_integrate_lib.extract import select_module; print(select_module('examples/structure/leaf.sv').ports)"
```

The CLI entry point re-exports the historical Python API. Implementations live in
`scripts/soc_integrate_lib/`; MCP transport remains in `mcp_server.py`.
