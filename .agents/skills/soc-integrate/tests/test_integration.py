"""CLI-level behavior and real Verilator lint in disposable directories."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_parser import MODULE, SCRIPT


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def source(self, name, text):
        path = self.root / (name + '.sv')
        path.write_text(text + '\n')
        return path

    def mapping(self, data):
        path = self.root / 'map.json'
        path.write_text(json.dumps(data))
        return path

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                cwd=self.root, text=True, capture_output=True, timeout=30)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def lint(self, *files, top='top'):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', top,
                                 *map(str, files)], cwd=self.root, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / 'obj_dir').exists())

    def pair(self, width=8):
        a = self.source('producer', 'module producer #(parameter WIDTH=8)(input clk, input rst_n, input en, output reg [WIDTH-1:0] q); always @(posedge clk or negedge rst_n) if (!rst_n) q <= 0; else if(en) q <= q + 1\'b1; endmodule')
        b = self.source('consumer', f'module consumer(input clk, input rst_n, input [{width-1}:0] data_i, output reg y); always @(posedge clk or negedge rst_n) if (!rst_n) y <= 0; else y <= &data_i; endmodule')
        mapping = self.mapping({'mappings': {'consumer.data_i': 'q'}})
        return a, b, mapping

    def test_default_no_sidecars_and_clean_lint(self):
        a, b, mapping = self.pair()
        result = self.cli('integrate', a, b, '--map', mapping, '-n', 'top', '-o', 'top.sv')
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertFalse((self.root / 'top.integrate.json').exists())
        self.assertFalse((self.root / 'top.integrate.csv').exists())
        code = (self.root / 'top.sv').read_text()
        self.assertTrue(code.endswith('\n'))
        self.assertNotIn('[8-1:0]', code)
        self.assertIn('.data_i(q)', code)
        self.assertNotIn('lint_off PINCONNECTEMPTY', code)
        self.lint(a, b, self.root / 'top.sv')

    def test_incompatible_same_name_types_exposed_separately(self):
        pkg = self.source('pkg', 'package pkg; typedef logic [7:0] word_t; endpackage')
        scalar = self.source('non_ansi', 'module non_ansi(a,y); input a; output y; assign y=a; endmodule')
        typed = self.source('pkg_typed', 'module pkg_typed(input pkg::word_t a, output wire y); assign y=&a; endmodule')
        result = self.cli('integrate', scalar, typed, '-n', 'top', '-o', 'top.sv', '--track', '--csv')
        self.assertIn('auto-share-incompatible', result.stderr)
        top = MODULE.extract_modules(self.root / 'top.sv')[0]
        self.assertEqual([n for _, _, n in top.ports],
                         ['u_non_ansi_a', 'u_non_ansi_y', 'u_pkg_typed_a', 'u_pkg_typed_y'])
        self.assertEqual(top.details['u_pkg_typed_a']['type'], 'pkg::word_t')
        checks = json.loads((self.root / 'top.integrate.json').read_text())['checks']
        self.assertTrue(any(c['code'] == 'auto-share-incompatible' for c in checks))
        with (self.root / 'top.integrate.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertTrue(all(not r['Shared_With'] for r in rows if r['Port'] == 'a'))
        self.lint(pkg, scalar, typed, self.root / 'top.sv')

    def test_same_name_port_compatibility_uses_width_type_and_dimensions(self):
        cases = [
            ('input [3:0] a', 'input [7:0] a'),
            ('input logic [3:0] a', 'input logic signed [3:0] a'),
            ('input logic [3:0] a [0:1]', 'input logic [3:0] a [0:2]'),
        ]
        for left, right in cases:
            with self.subTest(left=left, right=right):
                a = self.source('a', f'module a({left}); endmodule')
                b = self.source('b', f'module b({right}); endmodule')
                result = self.cli('integrate', a, b, '-n', 'top', '-o', 'top.sv')
                self.assertIn('auto-share-incompatible', result.stderr)
                ports = MODULE.extract_modules(self.root / 'top.sv')[0].ports
                self.assertEqual([n for _, _, n in ports], ['u_a_a', 'u_b_a'])
        # Equivalent defaults, storage spelling and whitespace still auto-share.
        a = self.source('a', 'module a #(parameter N=8)(input wire [N-1:0] x, output y); assign y=&x; endmodule')
        b = self.source('b', 'module b(input logic unsigned [ 7 : 0 ] x, output y); assign y=&x; endmodule')
        result = self.cli('integrate', a, b, '-n', 'top', '-o', 'top.sv')
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertEqual([n for _, _, n in MODULE.extract_modules(self.root / 'top.sv')[0].ports],
                         ['x', 'u_a_y', 'u_b_y'])
        self.lint(a, b, self.root / 'top.sv')

    def test_intentional_empty_pins_have_local_lint_comments(self):
        mod = self.source('dut', 'module dut(input a, input optional_i, output y, output optional_o); assign y=a ^ optional_i; assign optional_o=a; endmodule')
        mapping = self.mapping({'mappings': {'dut.optional_i': '', 'dut.optional_o': None}})
        result = self.cli('integrate', mod, '--map', mapping, '-n', 'top', '-o', 'top.sv')
        self.assertIn('undriven-input', result.stderr)
        self.assertIn('unused-output', result.stderr)
        code = (self.root / 'top.sv').read_text()
        self.assertEqual(code.count('// verilator lint_off PINCONNECTEMPTY'), 2)
        self.assertEqual(code.count('// verilator lint_on PINCONNECTEMPTY'), 2)
        self.assertIn('// verilator lint_off PINCONNECTEMPTY\n        .optional_i(),\n'
                      '        // verilator lint_on PINCONNECTEMPTY', code)
        self.assertIn('// verilator lint_off PINCONNECTEMPTY\n        .optional_o()\n'
                      '        // verilator lint_on PINCONNECTEMPTY', code)
        self.lint(mod, self.root / 'top.sv')
        result = self.cli('update', 'top.sv', '--files', mod)
        self.assertIn('undriven-input', result.stderr)
        self.assertIn('unused-output', result.stderr)
        self.lint(mod, self.root / 'top.sv')

    def test_update_preserves_surviving_top_port_order_and_appends_new(self):
        counter = self.source('counter', 'module counter(input en, input gone, output y); assign y=en & gone; endmodule')
        other = self.source('other', 'module other(input x, output z); assign z=x; endmodule')
        top = self.root / 'top.sv'
        self.cli('integrate', counter, other, '-n', 'top', '-o', top)
        original_names = [n for _, _, n in MODULE.extract_modules(top)[0].ports]
        self.assertEqual(original_names, ['u_counter_en', 'u_counter_gone', 'u_counter_y', 'u_other_x', 'u_other_z'])
        # Expression dependencies are discovered after ordinary connections.
        top.write_text(top.read_text().replace('.en(u_counter_en)', ".en( u_counter_en & 1'b1 )"))
        counter.write_text('module counter(input new_i, output new_o, output y, input en); assign y=en & new_i; assign new_o=en; endmodule\n')
        self.cli('update', top, '--files', counter, other)
        updated_names = [n for _, _, n in MODULE.extract_modules(top)[0].ports]
        expected = [n for n in original_names if n != 'u_counter_gone'] + ['u_counter_new_i', 'u_counter_new_o']
        self.assertEqual(updated_names, expected)
        self.assertIn(".en( u_counter_en & 1'b1 )", top.read_text())
        self.lint(counter, other, top)
        self.cli('update', top, '--files', counter, other)
        self.assertEqual([n for _, _, n in MODULE.extract_modules(top)[0].ports], expected)

    def test_csv_and_tracking_independent(self):
        a, b, mapping = self.pair()
        self.cli('integrate', a, b, '--map', mapping, '-n', 'top', '-o', 'top.sv', '--csv')
        self.assertFalse((self.root / 'top.integrate.json').exists())
        with (self.root / 'top.integrate.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        clk = next(r for r in rows if r['Instance'] == 'u_producer' and r['Port'] == 'clk')
        self.assertEqual(clk['Shared_With'], 'u_consumer.clk')
        q = next(r for r in rows if r['Port'] == 'q')
        self.assertEqual(q['Shared_With'], 'u_consumer.data_i')
        self.assertIn('Checks', q)
        (self.root / 'top.integrate.csv').unlink()
        self.cli('integrate', a, b, '--map', mapping, '-n', 'top', '-o', 'top.sv', '--track')
        data = json.loads((self.root / 'top.integrate.json').read_text())
        self.assertEqual(data['checks'], [])
        self.assertFalse((self.root / 'top.integrate.csv').exists())
        self.assertTrue((self.root / 'top.integrate.json').read_bytes().endswith(b'\n'))

    def test_width_warning_no_silent_slice_and_strict(self):
        a, b, mapping = self.pair(4)
        result = self.cli('integrate', a, b, '--map', mapping, '-o', 'top.sv', '-n', 'top', '--csv', '--track')
        self.assertIn('width mismatch', result.stderr)
        self.assertIn('.data_i(q)', (self.root / 'top.sv').read_text())
        self.assertNotIn('q[3:0]', (self.root / 'top.sv').read_text())
        checks = json.loads((self.root / 'top.integrate.json').read_text())['checks']
        self.assertEqual(checks[0]['code'], 'width-mismatch')
        self.assertIn('width-mismatch', (self.root / 'top.integrate.csv').read_text())
        result = self.cli('integrate', a, b, '--map', mapping, '-o', 'strict.sv', '--strict', ok=False)
        self.assertIn('width mismatch', result.stderr)
        self.assertIn('strict check failed', result.stderr)
        self.assertFalse((self.root / 'strict.sv').exists())

    def test_regex_capture_templates_and_exact_precedence(self):
        mod = self.source('dma', 'module dma(input clk, output irq_o); assign irq_o=clk; endmodule')
        data = {'instances': [{'module': 'dma', 'instance': 'u_dma0'}, {'module': 'dma', 'instance': 'u_dma1'}],
                'mappings': {'u_dma1.irq_o': 'special'},
                'templates': [{'regex': r'u_dma(\d+)\.irq_o', 'value': 'dma_irq[$1]'},
                              {'glob': '*.irq_o', 'value': 'loser'}]}
        mapping = self.mapping(data)
        self.cli('integrate', mod, '--map', mapping, '-n', 'top', '-o', 'top.sv')
        code = (self.root / 'top.sv').read_text()
        self.assertIn('.irq_o(dma_irq[0])', code)
        self.assertIn('.irq_o(special)', code)
        extracted = json.loads(self.cli('extract-map', 'top.sv').stdout)
        self.assertEqual(extracted['templates'], data['templates'])
        self.assertNotIn('u_dma0.irq_o', extracted['mappings'])
        expanded = json.loads(self.cli('extract-map', 'top.sv', '--expand').stdout)
        self.assertEqual(expanded['mappings']['u_dma0.irq_o'], 'dma_irq[0]')
        self.cli('update', 'top.sv', '--files', mod)
        self.assertIn('.irq_o(dma_irq[0])', (self.root / 'top.sv').read_text())
        self.lint(mod, self.root / 'top.sv')

    def test_legacy_regex_key_and_glob_captures(self):
        mapping = MODULE.PortMap({'mappings': {r'u_dma(\d+).irq_o': 'dma_irq[$1]', 'glob:u_*.reset?': '$1_rst$2'}})
        self.assertEqual(mapping.lookup('u_dma2', 'dma', 'irq_o'), (True, 'dma_irq[2]'))
        self.assertEqual(mapping.lookup('u_cpu', 'cpu', 'reset0'), (True, 'cpu_rst0'))
        mapping = MODULE.PortMap({'templates': [{'glob': 'u_*.a', 'value': 'first_$1'}, {'regex': '.*', 'value': 'last'}]})
        self.assertEqual(mapping.lookup('u_cpu', 'cpu', 'a'), (True, 'first_cpu'))

    def test_constants_slices_and_unconnected(self):
        mod = self.source('dut', 'module dut(input [3:0] a, input b, input [7:0] c, input [7:0] d, input [7:0] e, input f, output y); assign y=&{a,b,c,d,e,f}; endmodule')
        data = {'mappings': {'dut.a': 'sig[7:4]', 'dut.b': 'sig[3]', 'dut.c': "8'hFF", 'dut.d': "'0", 'dut.e': "'1", 'dut.f': "1'b0", 'dut.y': None}}
        result = self.cli('integrate', mod, '--map', self.mapping(data), '-o', 'top.sv')
        code = (self.root / 'top.sv').read_text()
        self.assertIn('.y()', code)
        self.assertIn('.a(sig[7:4])', code)
        self.assertNotIn('width mismatch', result.stderr)
        self.assertIn('unused-output', result.stderr)
        data['mappings']['dut.f'] = ''
        result = self.cli('integrate', mod, '--map', self.mapping(data), '-o', 'top.sv')
        self.assertIn('undriven-input', result.stderr)
        self.cli('integrate', mod, '-n', 'top', '--map', self.mapping(data), '--strict', ok=False)

    def test_multiple_driver_and_disjoint_slices(self):
        a = self.source('a', 'module a(input x, output y); assign y=x; endmodule')
        b = self.source('b', 'module b(input x, output y); assign y=x; endmodule')
        mapping = self.mapping({'mappings': {'a.y': 'q', 'b.y': 'q'}})
        result = self.cli('integrate', a, b, '--map', mapping, '-o', 'top.sv')
        self.assertIn('multiple-driver', result.stderr)
        self.cli('integrate', a, b, '-n', 'top', '--map', mapping, '--strict', ok=False)
        mapping = self.mapping({'mappings': {'a.y': 'q[0]', 'b.y': 'q[1]'}})
        result = self.cli('integrate', a, b, '--map', mapping, '-n', 'top', '-o', 'top.sv')
        self.assertNotIn('multiple-driver', result.stderr)
        self.lint(a, b, self.root / 'top.sv')

    def test_cdc_and_synchronizer_annotations(self):
        a = self.source('a', 'module a(input clk_a, input x, output reg q); always @(posedge clk_a) q<=x; endmodule')
        b = self.source('b', 'module b(input b_clk, input q, output reg y); always @(posedge b_clk) y<=q; endmodule')
        result = self.cli('integrate', a, b, '-n', 'top', '-o', 'top.sv')
        self.assertIn('CDC crossing', result.stderr)
        for extra in ({'annotations': {'u_b.q': {'sync': True}}}, {'synchronizers': ['u_b.q']},
                      {'mappings': {'b.q': {'signal': 'q', 'sync': True}}}):
            result = self.cli('integrate', a, b, '--map', self.mapping(extra), '-o', 'top.sv')
            self.assertNotIn('CDC crossing', result.stderr)
        data = {'domains': {'u_a': 'common', 'u_b': {'clock': 'common'}}}
        result = self.cli('integrate', a, b, '--map', self.mapping(data), '-o', 'top.sv')
        self.assertNotIn('CDC crossing', result.stderr)
        self.cli('integrate', a, b, '-n', 'top', '--strict', ok=False)

    def test_per_port_clock_annotations_and_multiclock(self):
        a = self.source('a', 'module a(input clk_a, input x, output q); assign q=clk_a & x; endmodule')
        b = self.source('b', 'module b(input clk_b, input other_clk, input q, output y); assign y=q & clk_b & other_clk; endmodule')
        result = self.cli('integrate', a, b, '-o', 'top.sv')
        self.assertIn('cdc-unknown', result.stderr)
        mapping = self.mapping({'annotations': {'u_a.q': {'clock': 'clk_a'}, 'u_b.q': {'clock': 'clk_b'}}})
        result = self.cli('integrate', a, b, '--map', mapping, '-o', 'top.sv')
        self.assertIn('CDC crossing', result.stderr)

    def test_update_no_json_add_remove_and_preserve_expression(self):
        mod = self.source('dut', 'module dut #(parameter WIDTH=8)(input [WIDTH-1:0] a, input enable, output [WIDTH-1:0] y); assign y=enable ? a : 0; endmodule')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        top = self.root / 'top.sv'
        code = top.read_text().replace('.a(u_dut_a)', '.a( { u_dut_a[7:4], /* keep ), [ , */ u_dut_a[3:0] } )')
        code = code.replace('dut  u_dut (', 'dut #(.WIDTH(8)) u_dut (')
        top.write_text(code)
        mod.write_text('module dut #(parameter WIDTH=8)(input [WIDTH-1:0] a, input extra, output [WIDTH-1:0] y); assign y=extra ? a : 0; endmodule\n')
        result = self.cli('diff', top, '--files', mod)
        self.assertIn('[NEW] u_dut.extra', result.stdout)
        self.assertIn('[DEL] u_dut.enable', result.stdout)
        result = self.cli('update', top, '--files', mod)
        self.assertIn('[NEW] u_dut.extra', result.stdout)
        updated = top.read_text()
        self.assertIn('.a( { u_dut_a[7:4], /* keep ), [ , */ u_dut_a[3:0] } )', updated)
        self.assertIn('#(.WIDTH(8))', updated)
        self.assertNotIn('.enable(', updated)
        self.assertNotIn('input wire u_dut_enable', updated)
        self.assertTrue(updated.endswith('\n'))
        self.assertFalse((self.root / 'top.integrate.json').exists())
        self.assertFalse((self.root / 'top.integrate.csv').exists())
        self.lint(mod, top)
        extracted = json.loads(self.cli('extract-map', top).stdout)
        self.assertEqual(extracted['mappings']['u_dut.a'], ' { u_dut_a[7:4], /* keep ), [ , */ u_dut_a[3:0] } ')

    def test_update_width_direction_warning_and_sidecars(self):
        mod = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        mod.write_text('module dut(input [1:0] a, input y, output z); assign z=&a & y; endmodule\n')
        result = self.cli('diff', 'top.sv', '--files', mod)
        self.assertIn('[MOD] u_dut.a: width', result.stdout)
        self.assertIn('[MOD] u_dut.y: direction', result.stdout)
        result = self.cli('update', 'top.sv', '--files', mod, '--csv', '--track')
        self.assertIn('port-change', result.stderr)
        self.assertTrue((self.root / 'top.integrate.csv').exists())
        self.assertTrue((self.root / 'top.integrate.json').exists())
        self.assertTrue(json.loads((self.root / 'top.integrate.json').read_text())['checks'])
        self.lint(mod, self.root / 'top.sv')
        self.cli('update', self.root / 'top.integrate.json')

    def test_top_without_any_embedded_metadata(self):
        mod = self.source('dut', 'module dut #(parameter N=4)(input [N-1:0] a, input b, output [N-1:0] y); assign y=b ? a : 0; endmodule')
        self.source('top', 'module top(input [3:0] a, output [3:0] y); dut #(.N(4)) u0(.a( a ), .y(y)); endmodule')
        result = self.cli('diff', 'top.sv', '--files', mod)
        self.assertIn('[NEW] u0.b', result.stdout)
        self.cli('update', 'top.sv', '--files', mod)
        self.assertIn('.a( a )', (self.root / 'top.sv').read_text())
        self.lint(mod, self.root / 'top.sv')

    def test_snapshot_diff_and_spec_check(self):
        mod = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        self.cli('snapshot', mod, '-f', 'json')
        snapshot = self.root / 'dut_ports.json'
        self.cli('check', mod, snapshot)
        mod.write_text('module dut(input a, input b, output y); assign y=a & b; endmodule\n')
        self.assertIn('[NEW] dut.b', self.cli('diff', mod, snapshot).stdout)
        self.cli('check', mod, snapshot, ok=False)

    def test_check_top_graph(self):
        a, b, mapping = self.pair(4)
        self.cli('integrate', a, b, '--map', mapping, '-n', 'top', '-o', 'top.sv')
        result = self.cli('check', 'top.sv', '--files', a, b)
        self.assertIn('width mismatch', result.stderr)
        self.cli('check', 'top.sv', '--files', a, b, '--strict', ok=False)

    def test_cli_include_define_forms(self):
        inc = self.root / 'inc'
        inc.mkdir()
        (inc / 'defs.vh').write_text('`define WIDTH 8\n')
        mod = self.source('dut', '`include "defs.vh"\n`ifdef ENABLE\nmodule dut(input [`WIDTH-1:0] a, output [`WIDTH-1:0] y); assign y=a; endmodule\n`else\nmodule no(); endmodule\n`endif')
        result = self.cli('extract', mod, '+incdir+' + str(inc), '+define+ENABLE')
        self.assertEqual(json.loads(result.stdout)['module_name'], 'dut')
        self.cli('integrate', mod, '-I', inc, '-D', 'ENABLE=1', '-n', 'top', '-o', 'top.sv')
        self.lint('+incdir+' + str(inc), '+define+ENABLE', mod, self.root / 'top.sv')

    def test_native_interface_lint_and_update(self):
        fixture = Path(__file__).parent / 'fixtures' / 'bus_if.sv'
        interface = self.root / 'bus_if.sv'
        shutil.copyfile(fixture, interface)
        master = self.source('master', 'module master(input [7:0] x, bus_if.master s); assign s.data=x; endmodule')
        slave = self.source('slave', 'module slave(bus_if.slave s, output [7:0] y); assign y=s.data; endmodule')
        self.cli('integrate', master, slave, '-n', 'top', '-o', 'top.sv')
        code = (self.root / 'top.sv').read_text()
        self.assertIn('bus_if s ();', code)
        self.lint(interface, master, slave, self.root / 'top.sv')
        self.cli('update', 'top.sv', '--files', master, slave)
        self.lint(interface, master, slave, self.root / 'top.sv')
        slave.write_text('module slave(bus_if s, output [7:0] y); assign y=s.data; endmodule\n')
        self.cli('update', 'top.sv', '--files', master, slave)
        self.lint(interface, master, slave, self.root / 'top.sv')

    def test_package_and_non_ansi_lint(self):
        pkg = self.source('pkg', 'package pkg; typedef logic [7:0] word_t; endpackage')
        mod = self.source('dut', 'module dut(input pkg::word_t a, output pkg::word_t y); assign y=a; endmodule')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        self.assertIn('input pkg::word_t u_dut_a', (self.root / 'top.sv').read_text())
        self.lint(pkg, mod, self.root / 'top.sv')
        mod.write_text('module dut(a,y); input wire signed [7:0] a; output [7:0] y; reg [7:0] y; always @* y=a; endmodule\n')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        self.lint(mod, self.root / 'top.sv')

    def test_wrapper_lint_and_all_text_artifacts_newline(self):
        mod = self.source('dut', 'module dut #(parameter N=8)(input [N-1:0] a, output [N-1:0] y); assign y=a; endmodule')
        self.cli('wrap', mod, '-n', 'top', '-o', 'top.sv')
        self.lint(mod, self.root / 'top.sv')
        self.cli('instantiate', mod, '-o', 'instance.sv')
        self.cli('extract', mod, '-o', 'extract.json')
        self.cli('snapshot', mod)
        for file in self.root.iterdir():
            if file.is_file():
                self.assertTrue(file.read_bytes().endswith(b'\n'), str(file))


    def test_unsupported_existing_instance_syntax(self):
        mod = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        for code in ('dut u0(a,y);', 'dut u0(.*);', 'dut u0[2](.a(a),.y(y));',
                     'dut u0(.a(a),.a(a),.y(y));', 'dut u0(.a(a),.y(y)),u1(.a(a),.y(y));'):
            with self.subTest(code=code):
                top = self.source('top', 'module top(input a, output y); ' + code + ' endmodule')
                result = self.cli('update', top, '--files', mod, ok=False)
                self.assertIn('unsupported', result.stderr)

    def test_update_parameter_default_width_change(self):
        mod = self.source('dut', 'module dut #(parameter N=4)(input [N-1:0] a, output [N-1:0] y); assign y=a; endmodule')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        mod.write_text(mod.read_text().replace('N=4', 'N=8'))
        result = self.cli('diff', 'top.sv', '--files', mod)
        self.assertIn('width [3:0] -> [7:0]', result.stdout)
        self.cli('update', 'top.sv', '--files', mod)
        self.lint(mod, self.root / 'top.sv')

    def test_parameter_overrides_round_trip_and_repeated_instances(self):
        mod = self.source('dut', 'module dut #(parameter N=8)(input [N-1:0] a, output [N-1:0] y); assign y=a; endmodule')
        data = {'instances': [{'module': 'dut', 'instance': 'u0', 'parameters': {'N': '4'}},
                              {'module': 'dut', 'instance': 'u1', 'parameters': {'N': '4'}}]}
        self.cli('integrate', mod, '--map', self.mapping(data), '-n', 'top', '-o', 'top.sv')
        code = (self.root / 'top.sv').read_text()
        self.assertIn('u0_y', code)
        self.assertIn('u1_y', code)
        result = self.cli('update', 'top.sv', '--files', mod)
        self.assertNotIn('[MOD]', result.stdout)
        self.lint(mod, self.root / 'top.sv')
        self.cli('extract-map', 'top.sv', '-o', 'extracted.json')
        self.cli('integrate', mod, '--map', 'extracted.json', '-n', 'again', '-o', 'again.sv')
        self.lint(mod, self.root / 'again.sv', top='again')

    def test_wrapper_localparams_and_unpacked_lint(self):
        mod = self.source('dut', 'module dut #(parameter N=4)(input [L-1:0] a, output [L-1:0] y); localparam L=N*2; assign y=a; endmodule')
        self.cli('wrap', mod, '-n', 'top', '-o', 'top.sv')
        self.lint(mod, self.root / 'top.sv')
        mod.write_text('module dut(input logic signed [3:0] a [0:1], output logic signed [3:0] y [0:1]); assign y=a; endmodule\n')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv', '--force')
        self.lint(mod, self.root / 'top.sv')

    def test_invalid_template_capture_and_missing_include_cli(self):
        mod = self.source('dut', 'module dut(input a); endmodule')
        mapping = self.mapping({'templates': [{'regex': 'u_dut.a', 'value': '$2'}]})
        self.assertIn('missing capture $2', self.cli('integrate', mod, '-n', 'top', '--map', mapping, ok=False).stderr)
        mod.write_text('`include "missing.vh"\nmodule dut(); endmodule\n')
        self.assertIn('missing include', self.cli('extract', mod, ok=False).stderr)

    def test_annotation_only_mapping_keeps_default_connection(self):
        a = self.source('a', 'module a(input clk, input x, output q); assign q=clk & x; endmodule')
        b = self.source('b', 'module b(input clk, input q, output y); assign y=clk & q; endmodule')
        data = {'mappings': {'b.q': {'clock': 'clk', 'sync': True}}}
        result = self.cli('integrate', a, b, '--map', self.mapping(data), '-n', 'top', '-o', 'top.sv')
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertIn('.q(q)', (self.root / 'top.sv').read_text())
        self.cli('extract-map', 'top.sv', '-o', 'extracted.json')
        extracted = json.loads((self.root / 'extracted.json').read_text())
        self.assertTrue(extracted['mappings']['u_b.q']['sync'])
        self.lint(a, b, self.root / 'top.sv')

    def test_manual_expression_with_constant_is_preserved(self):
        mod = self.source('dut', 'module dut(input [7:0] a, output [7:0] y); assign y=a; endmodule')
        self.cli('integrate', mod, '-n', 'top', '-o', 'top.sv')
        top = self.root / 'top.sv'
        top.write_text(top.read_text().replace('.a(u_dut_a)', ".a( (u_dut_a ^ 8'hAA) )"))
        self.cli('update', top, '--files', mod)
        self.assertIn(".a( (u_dut_a ^ 8'hAA) )", top.read_text())
        self.lint(mod, top)

if __name__ == '__main__':
    unittest.main()
