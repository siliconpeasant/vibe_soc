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
            mapping = Path(directory) / 'map.json'
            mapping.write_text(json.dumps({'mappings': {'dmaa.a': 'x'}}))
            client = r"""
import asyncio, json, sys, shutil, re, ast
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
            skill_root = __import__('pathlib').Path(sys.argv[2]).parent
            docs = (skill_root/'SKILL.md').read_text()
            funcs = {node.name: node for node in ast.parse((skill_root/'mcp_server.py').read_text()).body
                     if isinstance(node, ast.FunctionDef) and node.name.startswith('soc_')}
            for name, schema in tools.items():
                documented = re.search(r'(?m)^'+name+r'\(([^\n]*)\)$', docs)
                assert documented, name
                params = [p.strip() for p in documented[1].split(',')]
                assert set(params) == set(schema['properties']), (name, params, schema)
                docstring = ast.get_docstring(funcs[name])
                match = re.search(r'Parameters: ([^\n]+)', docstring)
                assert match and match[1].split(', ') == params, (name, docstring)
            for flag in ('output', 'strict', 'port_map'):
                assert flag in tools['soc_remove']['properties']
            assert 'strict' in tools['soc_diff']['properties']

            for name in ('soc_integrate', 'soc_update'):
                for flag in ('csv', 'track', 'strict', 'lint_config'):
                    assert tools[name]['properties'][flag]['default'] is False
                assert 'include_dirs' in tools[name]['properties']
                assert 'defines' in tools[name]['properties']
                assert 'packages' in tools[name]['properties']
                assert 'library_dirs' in tools[name]['properties']
            for schema in tools.values():
                assert 'packages' in schema['properties']
            result = await session.call_tool('soc_extract', {'verilog_file': sys.argv[3]})
            assert not result.isError, result
            payload = json.loads(result.content[0].text)
            assert payload['module_name'] == 'dut', payload
            error = await session.call_tool('soc_integrate', dict(module_files=[sys.argv[3]],
                top_name='bad', output_file=str(__import__('pathlib').Path(sys.argv[3]).parent/'bad.sv'),
                port_map=sys.argv[4]))
            assert error.isError, error
            assert "port map references unknown module/instance 'dmaa' (known:" in error.content[0].text, error
            out = __import__('pathlib').Path(sys.argv[3]).parent/'top.sv'
            result = await session.call_tool('soc_integrate', dict(module_files=[sys.argv[3]],
                top_name='top', output_file=str(out), lint_config=True, library_dirs=[str(out.parent)]))
            assert not result.isError, result
            assert out.with_suffix('.vlt').exists()
            assert out.with_suffix('.lint.f').exists()
            assert str(out) not in out.with_suffix('.vlt').read_text()
            result = await session.call_tool('soc_update', dict(top_file=str(out), module_files=[sys.argv[3]],
                lint_config=True, library_dirs=[str(out.parent)]))
            assert not result.isError, result
            source = __import__('pathlib').Path(sys.argv[3])
            original = source.read_text()
            source.write_text(original.replace('input a', 'input [1:0] a'))
            result = await session.call_tool('soc_diff', dict(verilog_file=str(out), module_files=[str(source)], strict=True))
            assert result.isError, result
            source.write_text(original)
            destination = out.parent/'removed'
            destination.mkdir()
            result = await session.call_tool('soc_remove', dict(config_file=str(out), module_name='u_dut',
                module_files=[str(source)], output=str(destination/'top.sv'), strict=True, port_map=''))
            assert not result.isError, result
            assert 'module top ();' in (destination/'top.sv').read_text()
            result = await session.call_tool('soc_remove', dict(config_file=str(out), module_name='unknown', module_files=[str(source)]))
            assert result.isError, result
            fixture = __import__('pathlib').Path(sys.argv[5])
            result = await session.call_tool('soc_extract', dict(verilog_file=str(fixture/'peripheral.sv'),
                include_dirs=[str(fixture)], packages=[str(fixture/'demo_pkg.sv')], defines=['FEATURE=1']))
            assert not result.isError, result
            peripheral = json.loads(result.content[0].text)
            assert peripheral['param_dims']['Policy'] == '[NumRegs]', peripheral
            if shutil.which('verilator'):
                assert next(p for p in peripheral['ports'] if p['name']=='tl_i')['bits'] == 8, peripheral
            # Batch 2 keeps the protocol schema/call order while sorting packages.
            base = out.parent/'z_pkg.sv'
            base.write_text('package z_pkg; typedef logic [8:0] t; endpackage\n')
            dependent = out.parent/'a_pkg.sv'
            dependent.write_text('package a_pkg; typedef z_pkg::t t; endpackage\n')
            typed = out.parent/'typed.sv'
            typed.write_text('module typed(input a_pkg::t x, output y); assign y=|x; endmodule\n')
            result = await session.call_tool('soc_extract', dict(verilog_file=str(typed),
                packages=[str(dependent), str(base)]))
            assert not result.isError, result
            if shutil.which('verilator'):
                assert json.loads(result.content[0].text)['ports'][0]['bits'] == 9, result
            metadata = json.loads(out.read_text().splitlines()[1].split(': ', 1)[1])
            assert metadata['version'] == 2 and len(metadata['modules']) == 1, metadata
            source.write_text(original.replace('output y', 'output renamed').replace('assign y=', 'assign renamed='))
            result = await session.call_tool('soc_diff', dict(verilog_file=str(out), module_files=[str(source)], strict=True))
            assert result.isError and '[REN?] u_dut.y -> u_dut.renamed' in result.content[0].text, result
            source.write_text(original)
            print(json.dumps({'initialized': initialized.serverInfo.name,
                              'tools': sorted(tools), 'call': payload['module_name']}))
asyncio.run(main())
"""
            result = subprocess.run(['sh', str(LAUNCHER), '-c', client, str(LAUNCHER),
                                     str(SERVER), str(source), str(mapping), str(Path(__file__).parent / 'fixtures/ot_style')], cwd=ROOT, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence['call'], 'dut')
            self.assertIn('soc_check', evidence['tools'])
