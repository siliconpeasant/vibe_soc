"""Batch 1 review regressions: ownership, CLI contracts and compilation units."""
import ast
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import test_integration as helpers
from test_parser import MODULE


class Batch1(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def pair(self):
        a = self.source('a', 'module a(input x, output q); assign q=x; endmodule')
        b = self.source('b', 'module b(input q, output y); assign y=q; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', a, b, '-n', 'top')
        return a, b, top

    def test_conditional_owned_instance_preserves_ports_and_nets(self):
        a, b, top = self.pair()
        code = top.read_text().replace('    b  u_b (', '`ifdef USE_B\n    b  u_b (')
        code = code.replace('    );\nendmodule', '    );\n`endif\nendmodule')
        top.write_text(code)
        before = MODULE.parse_top(top)[3].ports
        result = self.cli('update', top, '--files', a, b)
        self.assertIn('conditional-preserved', result.stderr)
        self.assertEqual(before, MODULE.parse_top(top)[3].ports)
        self.assertIn('wire q;', top.read_text())
        self.assertEqual(top.read_text().count('b  u_b ('), 1)
        first = top.read_bytes()
        self.cli('update', top)
        self.assertEqual(first, top.read_bytes())
        self.lint('-DUSE_B', a, b, top)
        self.cli('remove', top, 'u_b', '--files', a, b)
        self.assertNotIn('b  u_b (', top.read_text())
        self.lint(a, top)

    def test_remove_instance_module_map_cleanup_empty_and_unknown(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        mapping = self.mapping({'instances': [{'module': 'dut', 'instance': f'u{i}'} for i in range(2)],
            'mappings': {'u0.a': 'a0', 'dut.y': 'q'},
            'templates': [{'regex': r'u0\.y', 'value': 'q'}, {'glob': 'u?.a', 'value': 'a$1'}],
            'annotations': {'u0.a': {'sync': True}}, 'domains': {'u0': 'c'}, 'synchronizers': ['u0']})
        top = self.root/'top.sv'
        # Separate outputs so removal is lint clean.
        data = json.loads(mapping.read_text()); data['mappings'].pop('dut.y'); mapping.write_text(json.dumps(data))
        self.cli('integrate', dut, '-n', 'top', '--map', mapping)
        self.cli('remove', top, 'u0', '--files', dut, '-o', self.root/'other.sv', '-n', 'other')
        self.assertIn('u0', top.read_text())  # alternate destination leaves original alone
        other = self.root/'other.sv'
        meta = MODULE.parse_top(other)[2]['port_map']
        self.assertNotIn('u0.a', meta['mappings'])
        self.assertEqual(meta['templates'], [{'glob': 'u?.a', 'value': 'a$1'}])
        self.assertEqual(meta['instances'], [{'module': 'dut', 'instance': 'u1'}])
        self.assertEqual(meta['synchronizers'], [])
        self.lint(dut, other, top='other')
        self.cli('remove', other, 'dut', '--files', dut)
        self.assertEqual(MODULE.parse_top(other)[3].ports, [])
        self.assertIn('module other ();', other.read_text())
        self.lint(other, top='other')
        before = other.read_bytes()
        self.assertIn('unknown', self.cli('remove', top, 'missing', '--files', dut, ok=False).stderr)
        self.assertEqual(before, other.read_bytes())

    def test_regenerate_ownership_guard_and_fewer_modules(self):
        a, b, top = self.pair()
        self.cli('integrate', a, '-o', top)
        self.assertNotIn('u_b', top.read_text())
        self.assertNotIn('soc-integrate:user begin', top.read_text())
        self.lint(a, top)
        manual = self.source('manual', 'module manual(); endmodule')
        manual.write_text('module manual(); unknown u(.*); endmodule\n')
        before = manual.read_bytes()
        self.assertIn('--force', self.cli('integrate', a, '-o', manual, ok=False).stderr)
        self.assertEqual(before, manual.read_bytes())
        self.cli('integrate', a, '-o', manual, '--force')
        self.lint(a, manual, top='manual')

    def test_vendor_waivers_do_not_hide_user_or_top_warnings(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        vendor = self.root/'vendor'; vendor.mkdir()
        dep = vendor/'dep.sv'; dep.write_text('module dep(input a, output y); wire stray; assign y=a; endmodule\n')
        user = self.source('user', 'module user(input b, output z); wire user_warning; assign z=b; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', dep, user, '-o', top, '--lint-config', '-I', self.root)
        config, manifest = top.with_suffix('.vlt'), top.with_suffix('.lint.f')
        self.assertNotIn(str(user), config.read_text())
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top', str(config), '-f', str(manifest)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('user_warning', result.stderr)
        self.assertNotIn("'stray'", result.stderr)
        user.write_text(user.read_text().replace('wire user_warning;', ''))
        self.lint(config, '-f', manifest)
        top.write_text(top.read_text().replace('endmodule', 'wire top_warning;\nendmodule'))
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top', str(config), '-f', str(manifest)], cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('top_warning', result.stderr)
        # An explicit vendor directory outside a vendor/ component opts in.
        self.cli('update', top, '--files', dep, user, '--lint-config', '--vendor-dir', self.root)
        self.assertNotIn(str(top), config.read_text())
        self.assertIn(str(user), config.read_text())

    def test_preprocess_once_cross_file_define_order_and_locations(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        a = self.source('a', '`define WIDTH 4\nmodule a(input [`WIDTH-1:0] x, output y); assign y=|x; endmodule')
        b = self.source('b', 'module b(input [`WIDTH-1:0] x, output y); assign y=|x; endmodule')
        run = MODULE.subprocess.run
        calls = []
        def record(command, **kwargs):
            calls.append(command)
            return run(command, **kwargs)
        with patch.object(MODULE.subprocess, 'run', side_effect=record):
            modules = MODULE.extract_sources([a, b])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][-2:], [str(a), str(b)])
        self.assertEqual(modules[str(b)][0].ports[0][1], '[3:0]')
        self.assertEqual(modules[str(b)][0].details['x']['file'], str(b))
        self.assertEqual(modules[str(b)][0].details['x']['line'], 1)
        with self.assertRaisesRegex(ValueError, 'undefined macro'):
            MODULE.extract_sources([b, a])
        header = self.root/'bad.svh'; header.write_text('\ninput struct packed {logic a;} x\n')
        b.write_text('module b(\n`include "bad.svh"\n); endmodule\n')
        error = self.cli('integrate', a, b, '-n', 'top', ok=False).stderr
        self.assertIn(f'{header}:2:', error)
        self.assertNotIn('Traceback', error)
        self.assertNotIn('soc-integrate-', error)

    def test_type_resolution_errors_name_original_header(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        pkg = self.source('pkg', 'package pkg; typedef logic ok_t; endpackage')
        header = self.root/'header.svh'
        header.write_text('\nmodule dut(\ninput pkg::missing_t a\n); endmodule\n')
        dut = self.source('dut', '`include "header.svh"')
        result = self.cli('extract', dut, '--package', pkg, ok=False)
        self.assertIn(f'{header}:3:', result.stderr)
        self.assertNotIn('soc-integrate-', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_filelist_defaults_and_diagnostic_channels(self):
        inc = self.root/'inc'; inc.mkdir()
        lib = self.root/'lib'; lib.mkdir()
        (inc/'width.svh').write_text('`define W 4\n')
        dut = self.source('dut', '`include "width.svh"\nmodule dut(input [`W-1:0] a, output y); assign y=|a; endmodule')
        filelist = self.root/'sources.f'
        filelist.write_text('# comment\n/* block comment */\n+incdir+inc\n+define+FEATURE=1\n-I inc\n-D OTHER=1\n-y lib\n// comment\ndut.sv // source\n')
        result = self.cli('integrate', '-f', filelist, '-o', 'derived.sv', '--lint-config')
        self.assertNotIn('Checks:', result.stdout)
        self.assertIn('Checks:', result.stderr)
        self.assertTrue((self.root/'derived.sv').exists())
        self.assertIn('module derived (', (self.root/'derived.sv').read_text())
        self.lint(self.root/'derived.vlt', '-f', self.root/'derived.lint.f', top='derived')
        self.cli('integrate', dut, '-I', inc, '-n', 'named')
        self.assertTrue((self.root/'named.sv').exists())
        self.assertIn('-n NAME or -o OUTPUT', self.cli('integrate', dut, '-I', inc, ok=False).stderr)
        for content in ('-I\n', '-f sources.f\n', '-unknown x\n'):
            filelist.write_text(content)
            self.cli('integrate', '-f', filelist, '-n', 'bad', ok=False)

    def test_errors_regex_missing_and_module_selection(self):
        result = self.cli('extract', self.root/'absent.sv', ok=False)
        self.assertIn('absent.sv', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule\nmodule alt(input b, output z); assign z=b; endmodule')
        self.assertEqual(json.loads(self.cli('extract', dut, '-m', 'alt').stdout)['module_name'], 'alt')
        self.cli('integrate', dut, '-n', 'top')
        self.assertIn('not found', self.cli('check', self.root/'top.sv', '--files', dut, '-m', 'wrong', ok=False).stderr)
        for template in ({'templates': [{'regex': '[broken', 'value': 'q'}]}, {'mappings': {'regex:[broken': 'q'}}):
            mapping = self.mapping(template)
            error = self.cli('integrate', dut, '-n', 'bad', '--map', mapping, ok=False).stderr
            self.assertIn("template '[broken'", error)
            self.assertNotIn('Traceback', error)
        self.cli('integrate', dut, '-n', 'bad', '-m', 'alt', ok=False)

    def test_documented_mcp_parameter_names_match_functions(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root/'mcp_server.py').read_text())
        docs = (root/'SKILL.md').read_text()
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith('soc_'):
                match = re.search(r'(?m)^' + node.name + r'\(([^\n]*)\)$', docs)
                self.assertIsNotNone(match, node.name)
                self.assertEqual([arg.arg for arg in node.args.args], [p.strip() for p in match[1].split(',')], node.name)
                self.assertIsNotNone(ast.get_docstring(node), node.name)
