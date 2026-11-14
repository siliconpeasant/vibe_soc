"""Exercise the installed MCP runtime, protocol initialization and real CLI call."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LAUNCHER = ROOT / 'scripts' / 'mcp_python.sh'
SERVER = ROOT / '.agents' / 'skills' / 'soc-integrate' / 'mcp_server.py'


class MCPStdioTest(unittest.TestCase):
    def test_stdio_initialize_list_and_call(self):
        probe = subprocess.run(['sh', str(LAUNCHER), '-c', 'import mcp'], cwd=ROOT,
                               capture_output=True, text=True, timeout=30)
        if probe.returncode:
            self.skipTest('mcp not importable in configured runtime: ' + probe.stderr)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'dut.sv'
            source.write_text('module dut(input a, output y); assign y=a; endmodule\n')
            client = """
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command='sh', args=[sys.argv[1], sys.argv[2]])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialized = await session.initialize()
            listing = await session.list_tools()
            tools = {tool.name: tool.inputSchema for tool in listing.tools}
            assert 'soc_check' in tools, tools
            for name in ('soc_integrate', 'soc_update'):
                for flag in ('csv', 'track', 'strict'):
                    assert tools[name]['properties'][flag]['default'] is False
                assert 'include_dirs' in tools[name]['properties']
                assert 'defines' in tools[name]['properties']
            result = await session.call_tool('soc_extract', {'verilog_file': sys.argv[3]})
            assert not result.isError, result
            payload = json.loads(result.content[0].text)
            assert payload['module_name'] == 'dut', payload
            print(json.dumps({'initialized': initialized.serverInfo.name,
                              'tools': sorted(tools), 'call': payload['module_name']}))
asyncio.run(main())
"""
            result = subprocess.run(['sh', str(LAUNCHER), '-c', client, str(LAUNCHER),
                                     str(SERVER), str(source)], cwd=ROOT, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence['call'], 'dut')
            self.assertIn('soc_check', evidence['tools'])
