"""Regressions for the integration review; fixtures are original, not vendor RTL."""
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from test_parser import MODULE
import test_integration as helpers

FIXTURES = Path(__file__).parent / 'fixtures' / 'ot_style'


class ReviewRegressions(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def test_01_function_macros_in_header_and_body(self):
        source = FIXTURES / 'peripheral.sv'
        with patch.object(MODULE.shutil, 'which', return_value=None):
            mod = MODULE.select_module(source)
            self.assertEqual(mod.name, 'peripheral')
            header = self.source('header', '`define WIDTH(n) ((n)*2)\nmodule header(input [`WIDTH(4)-1:0] x); endmodule')
            with self.assertRaisesRegex(ValueError, r'header.sv:2:.*function-like macro.*install verilator'):
                MODULE.select_module(header)
        if shutil.which('verilator'):
            mod = MODULE.select_module(source, include_dirs=[FIXTURES], packages=[FIXTURES / 'demo_pkg.sv'])
            self.assertEqual(mod.details['tl_i']['bits'], 8)
            mod = MODULE.select_module(header)
            self.assertEqual(MODULE.bit_width(mod.ports[0][1]), 8)

    def test_01_fallback_multiline_macros_and_header_diagnostics(self):
        source = self.source('dut', '`define BODY(x) \\\n  `UNKNOWN_INTERNAL(x) \\\n  module not_a_module(input struct {logic z;} bad); endmodule\nmodule dut(input a);\n `BODY(a)\n `UNDEFINED_ASSERT(a)\nendmodule')
        with patch.object(MODULE.shutil, 'which', return_value=None):
            self.assertEqual(MODULE.select_module(source).ports, [('input', '', 'a')])
            source.write_text('`define WIDTH(n) n\nmodule dut #(parameter N=`WIDTH(4))(input [N-1:0] a); endmodule\n')
            with self.assertRaisesRegex(ValueError, r'dut.sv:2:.*function-like macro.*install verilator'):
                MODULE.select_module(source)

    def test_01_named_vector_width_is_not_duplicated(self):
        dut = self.source('dut', 'module dut(input demo_pkg::enable_t enable_i, output demo_pkg::enable_t enable_o); assign enable_o=enable_i; endmodule')
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        self.cli('integrate', dut, '--package', FIXTURES / 'demo_pkg.sv', '-n', 'top', '-o', 'top.sv')
        code = (self.root / 'top.sv').read_text()
        self.assertIn('input demo_pkg::enable_t dut_enable_i', code)
        self.lint(FIXTURES / 'demo_pkg.sv', dut, self.root / 'top.sv')

    def test_02_header_import_and_unpacked_parameter_wrapper(self):
        mod = MODULE.select_module(FIXTURES / 'peripheral.sv')
        self.assertEqual(mod.imports, 'import demo_pkg::*;')
        self.assertEqual(mod.param_dims['Policy'], '[NumRegs]')
        wrapper = MODULE.generate_wrapper(mod, 'top')
        self.assertIn('parameter policy_t Policy[NumRegs]', wrapper)
        self.assertIn('import demo_pkg::*;', wrapper)
        (self.root / 'top.sv').write_text(wrapper)
        self.lint('-I' + str(FIXTURES), FIXTURES / 'demo_pkg.sv', FIXTURES / 'peripheral.sv', self.root / 'top.sv')

    def test_02_imported_unqualified_type_in_generated_top(self):
        dut = self.source('dut', "module dut import demo_pkg::*; (input h2d_t request_i, output h2d_t response_o); assign response_o=request_i ^ h2d_t'(NumRegs); endmodule")
        self.cli('integrate', dut, '--package', FIXTURES / 'demo_pkg.sv', '-n', 'top', '-o', 'top.sv')
        self.assertIn('input demo_pkg::h2d_t dut_request_i', (self.root / 'top.sv').read_text())
        self.lint(FIXTURES / 'demo_pkg.sv', dut, self.root / 'top.sv')

    def test_03_pads_buses_and_structs_need_opt_in(self):
        dut = self.source('dut', 'module dut(input clk, input rst_n, inout pad, input tl_i, input data_req, input axi_aw, input apb_addr, input ahb_addr, input demo_pkg::h2d_t config_i, input custom_t state_i); endmodule')
        mod = MODULE.select_module(dut)
        data = {'instances': [{'module': 'dut', 'instance': 'u0'}, {'module': 'dut', 'instance': 'u1'}]}
        instances = MODULE.default_instances([mod], data)
        _, rows, checks, _, _ = MODULE.build_top(instances, map_data=data)
        for name in ('clk', 'rst_n'):
            self.assertEqual({r['signal'] for r in rows if r['port'] == name}, {name})
        for name in ('pad', 'tl_i', 'data_req', 'axi_aw', 'apb_addr', 'ahb_addr', 'config_i', 'state_i'):
            self.assertEqual(len({r['signal'] for r in rows if r['port'] == name}), 2)
            self.assertTrue(any(c['code'] == 'auto-share-blocked' and any(p.endswith('.' + name) for p in c['ports']) for c in checks))
        data['mappings'] = {'u0.config_i': 'config', 'u1.config_i': 'config', 'u0.pad': 'pad', 'u1.pad': 'pad'}
        _, _, checks, shared, _ = MODULE.build_top(instances, map_data=data)
        self.assertEqual(shared['config'], ['u0.config_i', 'u1.config_i'])
        self.assertTrue(any(c['code'] == 'explicit-bus-share' for c in checks))

    def test_04_indexed_part_selects_arithmetic_and_lint(self):
        dut = self.source('dut', 'module dut(input clk, output [7:0] rdata); assign rdata={8{clk}}; endmodule')
        for sign, base in (('+', '$1*8'), ('-', '($1+1)*8-1')):
            with self.subTest(sign=sign):
                data = {'instances': [{'module': 'dut', 'instance': f'u{i}'} for i in range(4)],
                        'templates': [{'regex': r'u(\d+)\.rdata', 'value': f'rdata[{base} {sign}: 8]'}]}
                result = self.cli('integrate', dut, '--map', self.mapping(data), '-n', 'top', '-o', 'top.sv')
                self.assertIn('Checks: 0 warning(s)', result.stderr)
                self.assertIn('output wire [31:0] rdata', (self.root / 'top.sv').read_text())
                self.lint(dut, self.root / 'top.sv')
        self.assertEqual(MODULE.selection_interval('q[2*8 +: 8]'), (16, 23))
        self.assertEqual(MODULE.selection_interval('q[3*8-1 -: 8]'), (16, 23))

    def test_05_absolute_port_lines_with_colliding_substrings(self):
        source = self.source('clk', '// clk a y\n\nmodule clk(\n input clk,\n input a,\n output y\n);\nendmodule')
        for fallback in (False, True):
            with self.subTest(fallback=fallback):
                context = patch.object(MODULE.shutil, 'which', return_value=None) if fallback else patch.dict('os.environ', {})
                with context:
                    mod = MODULE.select_module(source)
                self.assertEqual({n: d['line'] for n, d in mod.details.items()}, {'clk': 4, 'a': 5, 'y': 6})
        mod = MODULE.select_module(FIXTURES / 'peripheral.sv')
        self.assertEqual({n: d['line'] for n, d in mod.details.items()}, {'clk_i': 9, 'rst_ni': 10, 'tl_i': 11, 'data_o': 12})
        legacy = self.source('legacy', '// a\nmodule legacy(a,y);\n input a;\n output y;\nendmodule')
        self.assertEqual({n: d['line'] for n, d in MODULE.select_module(legacy).details.items()}, {'a': 3, 'y': 4})

    def test_06_actionable_map_and_construct_errors(self):
        dut = self.source('dma', 'module dma(input a); endmodule')
        for data in ({'instances': [{'module': 'dmaa', 'instance': 'u0'}]}, {'mappings': {'dmaa.a': 'x'}}):
            result = self.cli('integrate', dut, '-n', 'top', '--map', self.mapping(data), ok=False)
            self.assertIn("port map references unknown module/instance 'dmaa' (known:", result.stderr)
            self.assertNotIn("Error: 'dmaa'", result.stderr)
        dut.write_text('module dma(\ninput struct packed {logic a;} x\n); endmodule\n')
        result = self.cli('extract', dut, ok=False)
        self.assertIn('dma.sv:2:', result.stderr)
        self.assertNotIn('unsupported unsupported', result.stderr)
        self.assertEqual(result.stderr.count('unsupported'), 1)

    def test_07_user_regions_and_unmanaged_statements(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        self.cli('integrate', dut, '-n', 'top', '-o', 'top.sv')
        top = self.root / 'top.sv'
        protected = '// soc-integrate:user begin\n  // Preserve tabs, whitespace and unknown syntax verbatim.\n\twire extra;  \n  assign extra = dut_a;\n  always_comb begin : custom\n    if (extra) $display("user module endmodule");\n  end\n  unknown_user u_other(.*);\n// soc-integrate:user end\n'
        outside = 'wire spare;\nassign spare = dut_a;\nalways @(dut_a) $display("outside");\nunknown_module extra_instance(.*);\n'
        top.write_text(top.read_text().replace('endmodule\n', outside + protected + 'endmodule\n'))
        result = self.cli('diff', top, '--files', dut)
        self.assertIn('[preserved-unmanaged]', result.stderr)
        self.assertIn('extra_instance', result.stderr)
        self.assertIn('preserved in an automatic user region', result.stderr)
        self.cli('update', top, '--files', dut)
        self.assertIn(protected, top.read_text())
        self.assertIn(outside, top.read_text())
        self.cli('update', top, '--files', dut)
        self.assertEqual(top.read_text().count(protected), 1)
        self.cli('integrate', dut, '-n', 'top', '-o', top)
        self.assertEqual(top.read_text().count(protected), 1)
        top.write_text(top.read_text().replace('// soc-integrate:user end', ''))
        self.assertRegex(self.cli('update', top, '--files', dut, ok=False).stderr, '(unterminated|nested) user region')

    def test_08_unmanaged_statement_has_one_semicolon_and_separator(self):
        dut = self.source('dut', 'module dut(input a); endmodule')
        self.cli('integrate', dut, '-n', 'top', '-o', 'top.sv')
        top = self.root / 'top.sv'
        statement = "wire stray_w = 1'b0;"
        top.write_text(top.read_text().replace('endmodule\n', statement + '\nendmodule\n'))
        line = top.read_text().splitlines().index(statement) + 1
        for command in ('diff', 'check', 'update'):
            with self.subTest(command=command):
                result = self.cli(command, top, '--files', dut)
                self.assertIn(f'Warning [preserved-unmanaged]: {top}:{line}: {statement} | '
                              'preserved in an automatic user region\n', result.stderr)
                self.assertEqual(result.stderr.count(statement), 1)
                self.assertNotIn(';;', result.stderr)

    def test_09_invalid_snapshot_and_map_json_errors(self):
        dut = self.source('dma', 'module dma(input a); endmodule')
        self.cli('integrate', dut, '-n', 'top', '-o', 'top.sv')
        top = self.root / 'top.sv'
        original = top.read_text()
        for command in ('diff', 'check'):
            with self.subTest(command=command):
                result = self.cli(command, top, dut, ok=False)
                self.assertIn(f'{dut}: not a valid snapshot JSON', result.stderr)
                self.assertIn('pass RTL via --files', result.stderr)
                self.assertNotIn('Error: Expecting value', result.stderr)
        invalid = self.root / 'invalid.json'
        for contents in ('{', '[]', dut.read_text()):
            invalid.write_text(contents)
            for command, args, kind in (
                ('integrate', (dut, '--map', invalid, '-o', top), 'port map'),
                ('update', (top, '--files', dut, '--map', invalid), 'port map'),
                ('update', (invalid, '--files', dut), 'update config'),
                ('diff', (top, invalid), 'snapshot'),
            ):
                with self.subTest(command=command, contents=contents, kind=kind):
                    result = self.cli(command, *args, ok=False)
                    self.assertIn(f'{invalid}: not a valid {kind} JSON', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(top.read_text(), original)

    def test_10_numeric_unpacked_dimensions_have_known_total_bits(self):
        for packed, unpacked, bits in (
            ('[7:0]', '[4]', 32),
            ('[7:0]', '[3:0]', 32),
            ('[7:0]', '[1:4]', 32),
            ('[7:0]', '[4][2:0]', 96),
            ('[1:0][3:0]', '[2][0:2]', 48),
            ('', '[4]', 4),
            ('[W-1:0]', '[N][N-1:0]', 128),
        ):
            with self.subTest(packed=packed, unpacked=unpacked):
                dut = self.source('gpio_b', f'module gpio_b #(parameter W=8, N=4) '
                                  f'(input wire {packed} mem_cfg {unpacked}); endmodule')
                mod = MODULE.select_module(dut)
                code, rows, checks, _, _ = MODULE.build_top(MODULE.default_instances([mod], {}))
                self.assertEqual(rows[0]['bits'], bits)
                self.assertFalse(any(c['code'] == 'width-unknown' for c in checks), checks)
                top = MODULE.parse_module('soc_top', code)
                self.assertEqual(top.ports[0][1], MODULE.resolve_param_width(packed, mod.params))
                self.assertEqual(top.details['gpio_b_mem_cfg']['unpacked'],
                                 MODULE.resolve_param_width(unpacked, mod.params))
                result = self.cli('integrate', dut, '--strict', '-n', 'top', '-o', 'top.sv')
                self.assertIn('Checks: 0 warning(s)', result.stderr)
                self.cli('update', self.root / 'top.sv', '--files', dut, '--strict')
        for packed, unpacked in (('[7:0]', '[DEPTH]'), ('[7:0]', '[0:LAST]'),
                                 ('[WIDTH-1:0]', '[4]')):
            with self.subTest(packed=packed, unpacked=unpacked):
                dut = self.source('gpio_b', f'module gpio_b(input wire {packed} mem_cfg {unpacked}); endmodule')
                mod = MODULE.select_module(dut)
                _, rows, checks, _, _ = MODULE.build_top(MODULE.default_instances([mod], {}))
                self.assertIsNone(rows[0]['bits'])
                self.assertTrue(any(c['code'] == 'width-unknown' and
                                    c['ports'] == ['u_gpio_b.mem_cfg'] for c in checks), checks)
