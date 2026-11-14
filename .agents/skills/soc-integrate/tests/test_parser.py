from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'soc_integrate.py'
SPEC = importlib.util.spec_from_file_location('soc_integrate_cli', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerilogParserTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def parse(self, text, **options):
        path = self.root / 'dut.sv'
        path.write_text(text)
        return MODULE.extract_modules(path, **options)[0]

    def test_ansi_continuations(self):
        m = self.parse('module dut(input wire [7:0] a, b, output wire y); endmodule\n')
        self.assertEqual(m.ports, [('input', '[7:0]', 'a'), ('input', '[7:0]', 'b'), ('output', '', 'y')])

    def test_non_ansi_redeclaration_and_order(self):
        m = self.parse('module dut(b,a,q,z); input wire signed [7:0] a,b; output q; reg q; inout logic z; endmodule\n')
        self.assertEqual(m.ports, [('input', '[7:0]', 'b'), ('input', '[7:0]', 'a'), ('output', '', 'q'), ('inout', '', 'z')])
        self.assertEqual(m.details['q']['type'], 'reg')
        self.assertEqual(m.details['a']['type'], 'wire signed')

    def test_parameters_defaults_localparams_and_widths(self):
        m = self.parse('module dut #(parameter integer WIDTH=8, N=WIDTH+2)(input [WIDTH-1:0] a); parameter X=3,Y=4; localparam L=X+1; endmodule\n')
        self.assertEqual(m.params[:2], [('WIDTH', '8', 'integer'), ('N', 'WIDTH+2', 'integer')])
        self.assertEqual(m.localparams, [('L', 'X+1', '')])
        self.assertEqual(m.ports[0][1], '[WIDTH-1:0]')
        self.assertEqual(MODULE.resolve_param_width('[WIDTH-1:0]', m.params), '[7:0]')
        self.assertEqual(MODULE.resolve_param_width('[8-1:0]'), '[7:0]')
        self.assertEqual(MODULE.resolve_param_width('[UNKNOWN-1:0]', m.params), '[UNKNOWN-1:0]')
        self.assertIn('[WIDTH-1:0]', MODULE.generate_wrapper(m))
        self.assertNotIn('.L(', MODULE.generate_instance(m))

    def test_package_and_local_types_and_unpacked(self):
        m = self.parse('module dut(input pkg::word_t a, output word_t b, input logic signed [3:0] x [0:1]); endmodule\n')
        self.assertEqual(m.details['a']['type'], 'pkg::word_t')
        self.assertEqual(m.details['b']['type'], 'word_t')
        self.assertEqual(m.details['x']['unpacked'], '[0:1]')
        text = MODULE.generate_wrapper(m)
        self.assertIn('input pkg::word_t a', text)
        self.assertIn('output word_t b', text)
        self.assertIn('logic signed [3:0] x [0:1]', text)

    def test_interface_and_modport(self):
        m = self.parse('module dut(bus_if.slave s, bus_if t); endmodule\n')
        self.assertEqual([p[0] for p in m.ports], ['interface', 'interface'])
        self.assertEqual(m.details['s']['type'], 'bus_if.slave')

    def test_preprocessor_include_macro_and_branches(self):
        inc = self.root / 'inc'
        inc.mkdir()
        (inc / 'defs.vh').write_text('`define WIDTH 8\n')
        m = self.parse('`include "defs.vh"\n`ifdef NO\nmodule bad(input struct {logic a;} x); endmodule\n`elsif YES\nmodule dut(input [`WIDTH-1:0] a); endmodule\n`else\nmodule other(); endmodule\n`endif\n', include_dirs=[inc], defines=['YES'])
        self.assertEqual(m.name, 'dut')
        self.assertEqual(m.ports[0][1], '[7:0]')
        m = self.parse('`ifndef YES\nmodule dut(); endmodule\n`else\nmodule no(); endmodule\n`endif\n')
        self.assertEqual(m.name, 'dut')

    def test_missing_include_diagnostic(self):
        with self.assertRaisesRegex(ValueError, r'dut.sv:1: missing include "absent.vh"'):
            self.parse('`include "absent.vh"\nmodule dut(); endmodule\n')

    def test_unsupported_ports_are_errors(self):
        for port in ('input struct packed {logic a;} x', 'input [3:0] x = 0', '.x(a)', 'input a garbage extra', 'interface bus x'):
            with self.subTest(port=port), self.assertRaisesRegex(ValueError, r'dut.sv:\d+: unsupported'):
                self.parse(f'module dut(\n{port}\n); endmodule\n')

    def test_missing_non_ansi_direction(self):
        with self.assertRaisesRegex(ValueError, 'without direction declaration'):
            self.parse('module dut(a,b); input a; endmodule\n')

    def test_unused_function_macro_define(self):
        self.assertEqual(self.parse('`define F(x) x\nmodule dut(); endmodule\n').name, 'dut')

    def test_unknown_macro_error(self):
        with self.assertRaisesRegex(ValueError, 'undefined macro'):
            self.parse('module dut(input [`UNKNOWN:0] a); endmodule\n')

    def test_nested_comment_and_module_words(self):
        m = self.parse('// module fake(a)\n/* module fake2(x); */\nmodule dut(input a); endmodule\n')
        self.assertEqual(m.name, 'dut')

    def test_macro_included_source_error_location(self):
        (self.root / 'bad.vh').write_text('module bad(input struct {logic a;} x); endmodule\n')
        with self.assertRaisesRegex(ValueError, r'bad.vh:1: unsupported'):
            self.parse('`include "bad.vh"\n')

    def test_multiple_storage_redeclarations(self):
        m = self.parse('module dut(a,q,r); input a; output q,r; reg q,r; endmodule\n')
        self.assertEqual(m.details['q']['type'], 'reg')
        self.assertEqual(m.details['r']['type'], 'reg')

    def test_unsupported_interface_array(self):
        with self.assertRaisesRegex(ValueError, 'interface array'):
            self.parse('module dut(bus_if.slave s [2]); endmodule\n')

    def test_clog2_parameter(self):
        self.assertEqual(MODULE.resolve_param_width('[N-1:0]', [('DEPTH', '16', ''), ('N', '$clog2(DEPTH)', '')]), '[3:0]')

    def test_nested_conditionals_and_undef(self):
        m = self.parse('`define A 1\n`ifdef A\n`ifndef B\n`define W 4\n`endif\n`endif\n`undef A\n`ifdef A\nmodule no(); endmodule\n`else\nmodule dut(input [`W-1:0] a); endmodule\n`endif\n')
        self.assertEqual(m.ports[0][1], '[3:0]')

    def test_malformed_conditionals(self):
        for text in ('`else\n', '`ifdef A\n', '`ifdef A\n`else\n`elsif B\n`endif\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.parse(text)

    def test_implicit_direction_on_value_types(self):
        m = self.parse('module dut(pkg::word_t a, type_t b); endmodule\n')
        self.assertEqual([p[0] for p in m.ports], ['input', 'input'])
        self.assertIn('input pkg::word_t a', MODULE.generate_wrapper(m))

    def test_body_parameters_and_packed_dimension_arithmetic(self):
        m = self.parse('module dut(a,y); parameter WIDTH=8, LANES=2; localparam MSB=WIDTH-1; input [LANES-1:0][MSB:0] a; output [15:0] y; assign y=a; endmodule\n')
        self.assertEqual(MODULE.resolve_param_width(m.ports[0][1], m.params + m.localparams), '[1:0][7:0]')
        self.assertEqual(MODULE.bit_width('[1:0][7:0]'), 16)


if __name__ == '__main__':
    unittest.main()
