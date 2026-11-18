"""Lossless refresh, concrete interface elaboration and scoped vendor lint."""
import json
import shutil
import subprocess
import unittest

import test_integration as helpers


class RemainingLimitations(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def test_lossless_unmanaged_and_idempotent_lint(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        helper = self.source('helper', 'module helper(input a, output y); assign y=a; endmodule')
        top = self.root / 'top.sv'
        self.cli('integrate', dut, '-n', 'top', '-o', top)
        # Every construct is semantically used; the helper is deliberately not
        # included in the set of managed modules during refresh.
        custom = '''  // User comment and whitespace stay byte identical.\x20\x20
\twire w;
  logic c;
  reg q;
  wire h;
  wire g;
  assign w = u_dut_a;
  always_comb begin : comb
    c = w;
  end
  always_ff @(posedge u_dut_a) begin : seq
    q <= c;
  end
  always @(q) $display("q=%b", q);
  helper u_helper (.a(q), .y(h));
  generate
    if (1) begin : gen_user
      dut u_nested (.a(h), .y(g));
    end
  endgenerate
`ifdef USER_FEATURE
  wire unused_feature = g;
`else
  wire unused_other = g;
`endif
  function automatic logic invert(input logic x);
    return ~x;
  endfunction
  task automatic report(input logic x);
    $display("x=%b", x);
  endtask
  always @(g) report(invert(g));
'''
        top.write_text(top.read_text().replace('endmodule\n', custom + 'endmodule\n'))
        line = top.read_text().splitlines().index('  // User comment and whitespace stay byte identical.  ') + 1
        result = self.cli('update', top, '--files', dut)
        self.assertIn(f'[preserved-unmanaged]: {top}:{line}:', result.stderr)
        self.assertIn(custom.encode(), top.read_bytes())
        first = top.read_bytes()
        self.cli('update', top, '--files', dut)
        self.assertEqual(first, top.read_bytes())
        self.lint(dut, helper, top)
        self.lint('-DUSER_FEATURE', dut, helper, top)
        self.cli('integrate', dut, '-n', 'top', '-o', top)
        self.assertEqual(first, top.read_bytes())

    def test_crlf_and_comments_only_preserved(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        top = self.root / 'top.sv'
        self.cli('integrate', dut, '-n', 'top', '-o', top)
        custom = b'  /* comments only, not executable RTL */\r\n\t// trailing spaces  \r\n'
        top.write_bytes(top.read_bytes().replace(b'endmodule\n', custom + b'endmodule\n'))
        self.cli('update', top, '--files', dut)
        self.assertIn(custom, top.read_bytes())
        first = top.read_bytes()
        self.cli('update', top, '--files', dut)
        self.assertEqual(first, top.read_bytes())
        self.lint(dut, top)

    def test_connected_custom_declarations_comments_and_file_directives(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', dut, '-n', 'top', '-o', top)
        custom = "  wire custom = u_dut_a;  /* keep initializer */\n"
        code = top.read_text().replace('.a(u_dut_a)', '.a(custom)').replace('.y(u_dut_y)', '// custom pin comment\n        .y(u_dut_y)')
        code = code.replace('endmodule\n', custom+'endmodule\n')
        preamble = '`default_nettype none\n// user file header\n'
        suffix = '\n`default_nettype wire\n'
        top.write_text(preamble+code.rstrip('\n')+suffix)
        self.cli('update', top, '--files', dut)
        self.assertIn(custom.encode(), top.read_bytes())
        self.assertIn('// custom pin comment', top.read_text())
        self.assertTrue(top.read_text().startswith(preamble))
        self.assertTrue(top.read_text().endswith(suffix))
        first = top.read_bytes()
        self.cli('update', top, '--files', dut)
        self.assertEqual(first, top.read_bytes())
        self.lint(dut, top)

    def test_manual_top_declarations_are_not_assumed_owned(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        custom = '  wire bridge; // preserve this declaration\n  assign bridge = a;\n'
        top = self.source('top', 'module top(input a, output y);\n'+custom+'  dut u0(.a(bridge), .y(y));\nendmodule')
        self.cli('update', top, '--files', dut)
        self.assertIn(custom.encode(), top.read_bytes())
        first = top.read_bytes()
        self.cli('update', top, '--files', dut)
        self.assertEqual(first, top.read_bytes())
        self.lint(dut, top)

    def interface(self):
        return self.source('bus_if', '''interface bus_if #(parameter int W=8)(input logic clk);
  logic [W-1:0] data;
  modport mp(input clk, data);
endinterface''')

    def test_legal_interface_forms_and_whole_arrays(self):
        interface = self.interface()
        for form in ('bus_if.mp', 'bus_if'):
            for dims in ('', '[N]', '[0:N-1]'):
                with self.subTest(form=form, dims=dims):
                    use = '|s.data' if not dims else '(|s[0].data) ^ (|s[1].data)'
                    clock = 's.clk' if not dims else 's[0].clk'
                    dut = self.source('dut', f'module dut {"#(parameter N=2)" if dims else ""}({form} s {dims}, output logic y); always_ff @(posedge {clock}) y <= {use}; endmodule')
                    mapping = self.mapping({'mappings': {'dut.s': 'bus'}, 'interfaces': {
                        'bus': {'type': 'bus_if', 'parameters': {'W': 32}, 'ports': {'clk': 'clk'}}}})
                    # Drive the interface data in a user block, leaving top lint enabled.
                    top = self.root / 'top.sv'
                    top.unlink(missing_ok=True)
                    self.cli('integrate', interface, dut, '--map', mapping, '-n', 'top', '-o', top)
                    text = top.read_text()
                    self.assertIn('bus_if #(.W(32)) bus', text)
                    if dims:
                        self.assertIn('[2]' if dims == '[N]' else '[0:1]', text)
                    drive = "assign bus.data = '0;" if not dims else "assign bus[0].data = '0;\nassign bus[1].data = '1;"
                    top.write_text(text.replace('endmodule\n', '// soc-integrate:user begin\n' + drive + '\n// soc-integrate:user end\nendmodule\n'))
                    self.lint(interface, dut, top)
                    extracted = json.loads(self.cli('extract', dut).stdout)
                    self.assertEqual(extracted['ports'][0]['type'], form)
                    self.assertIn('.s(s)', self.cli('instantiate', dut).stdout)
                    result = self.cli('diff', top, '--files', interface, dut)
                    self.assertNotIn('[MOD]', result.stdout)
                    self.cli('update', top, '--files', interface, dut)
                    first = top.read_bytes()
                    self.cli('update', top, '--files', interface, dut)
                    self.assertEqual(first, top.read_bytes())
                    self.lint(interface, dut, top)
                    self.cli('extract-map', top, '-o', 'roundtrip.json')
                    self.assertEqual(json.loads((self.root/'roundtrip.json').read_text())['interfaces']['bus']['parameters'], {'W': '32'})

    def test_generic_interfaces_extract_generate_refresh(self):
        interface = self.interface()
        for form in ('interface', 'interface.mp'):
            for dims in ('', '[N]', '[0:N-1]'):
                with self.subTest(form=form, dims=dims):
                    dut = self.source('dut', f'module dut #(parameter N=2)({form} s {dims}); endmodule')
                    extracted = json.loads(self.cli('extract', dut).stdout)
                    self.assertEqual(extracted['ports'][0]['type'], form)
                    self.assertEqual(extracted['ports'][0]['unpacked'], dims)
                    self.assertIn('.s(s)', self.cli('instantiate', dut).stdout)
                    mapping = self.mapping({'mappings': {'dut.s': 'bus'}, 'interfaces': {
                        'bus': {'type': 'bus_if', 'parameters': {'W': 32}}}})
                    top = self.root/'top.sv'
                    top.unlink(missing_ok=True)
                    self.cli('integrate', interface, dut, '--map', mapping, '-n', 'top', '-o', top)
                    self.assertIn('bus_if #(.W(32)) bus', top.read_text())
                    first = top.read_bytes()
                    self.cli('update', top, '--files', interface, dut)
                    self.assertEqual(first, top.read_bytes())
                    self.assertNotIn('[MOD]', self.cli('diff', top, '--files', interface, dut).stdout)

    def test_generic_interface_lint_when_supported_by_verilator(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        interface = self.interface()
        for form in ('interface', 'interface.mp'):
            dut = self.source('dut', f'module dut({form} s, output logic y); always_ff @(posedge s.clk) y <= |s.data; endmodule')
            mapping = self.mapping({'interfaces': {'s': {'type': 'bus_if'}}})
            top = self.root/'top.sv'
            top.unlink(missing_ok=True)
            self.cli('integrate', interface, dut, '--map', mapping, '-n', 'top', '-o', top)
            top.write_text(top.read_text().replace('endmodule\n', "// soc-integrate:user begin\nassign s.data = '0;\n// soc-integrate:user end\nendmodule\n"))
            result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top', str(interface), str(dut), str(top)], cwd=self.root, capture_output=True, text=True)
            if '%Error-UNSUPPORTED:' in result.stderr and 'Unsupported: generic interfaces' in result.stderr:
                self.skipTest('installed Verilator rejects legal generic interface ports (UNSUPPORTED); parser/generator/refresh coverage runs separately')
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_interface_template_elements_and_default_parameters(self):
        interface = self.interface()
        dut = self.source('dut', 'module dut(bus_if.mp s, output logic y); always_ff @(posedge s.clk) y <= |s.data; endmodule')
        mapping = self.mapping({'instances': [{'module': 'dut', 'instance': f'u_dut{i}'} for i in range(2)],
                                'templates': [{'regex': r'u_dut(\d+)\.s', 'value': 'bus[$1]'}]})
        top = self.root / 'top.sv'
        self.cli('integrate', interface, dut, '--map', mapping, '-n', 'top', '-o', top)
        self.assertIn('bus_if bus [0:1] (.clk(clk));', top.read_text())
        custom = "// soc-integrate:user begin\nassign bus[0].data = '0;\nassign bus[1].data = '1;\n// soc-integrate:user end\n"
        top.write_text(top.read_text().replace('endmodule\n', custom+'endmodule\n'))
        self.lint(interface, dut, top)
        self.cli('update', top, '--files', interface, dut)
        first = top.read_bytes()
        self.cli('update', top, '--files', interface, dut)
        self.assertEqual(first, top.read_bytes())
        self.lint(interface, dut, top)

    def test_equivalent_interface_array_dimensions_and_implicit_sources(self):
        interface = self.interface()
        dut = self.source('dut', 'module dut(bus_if.mp s [2], output logic y); always_ff @(posedge s[0].clk) y <= (|s[0].data) ^ (|s[1].data); endmodule')
        mapping = self.mapping({'mappings': {'dut.s': 'bus'}, 'interfaces': {
            'bus': {'parameters': {'W': 32}, 'unpacked': '[0:1]'}}})
        top = self.root/'top.sv'
        self.cli('integrate', interface, dut, '--map', mapping, '-n', 'top', '-o', top, '--track')
        custom = "// soc-integrate:user begin\nassign bus[0].data = '0;\nassign bus[1].data = '1;\n// soc-integrate:user end\n"
        top.write_text(top.read_text().replace('endmodule\n', custom+'endmodule\n'))
        first = top.read_bytes()
        self.cli('update', top)  # Recover both module and definition source paths.
        self.assertEqual(first, top.read_bytes())
        self.cli('update', self.root/'top.integrate.json')
        self.assertEqual(first, top.read_bytes())
        self.lint(interface, dut, top)

    def test_manual_interface_overrides_and_extra_interface_preserved(self):
        interface = self.interface()
        dut = self.source('dut', 'module dut(bus_if.mp s, output logic y); always_ff @(posedge s.clk) y <= |s.data; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', interface, dut, '-n', 'top', '-o', top)
        top.write_text(top.read_text().replace('bus_if s (.clk(clk));', 'bus_if #(.W(32)) s (.clk(clk));'))
        custom = "  bus_if #(.W(16)) unused_custom_bus (.clk(clk));\n  assign s.data = '0;\n"
        top.write_text(top.read_text().replace('endmodule\n', custom+'endmodule\n'))
        self.cli('update', top, '--files', interface, dut)
        self.assertIn(custom.encode(), top.read_bytes())
        self.assertIn('bus_if #(.W(32)) s (.clk(clk));', top.read_text())
        first = top.read_bytes()
        self.cli('update', top, '--files', interface, dut)
        self.assertEqual(first, top.read_bytes())
        self.cli('extract-map', top, '-o', 'roundtrip.json')
        data = json.loads((self.root/'roundtrip.json').read_text())
        self.assertEqual(data['interfaces']['s']['parameters']['W'], '32')
        # This test deliberately keeps an unused custom interface; no waiver is
        # added for it. Clean interface integrations are linted by the tests above.

    def test_vendor_config_positive_and_top_warning_negative(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        vendor_dir = self.root / 'vendor space'
        vendor_dir.mkdir()
        vendor = vendor_dir / 'dut.sv'
        vendor.write_text('module dut(input a, output y); wire stray; assign y=a; endmodule\n')
        pkg = vendor_dir / 'pkg.sv'
        pkg.write_text('package pkg; parameter int Unused=4; endpackage\n')
        top = self.root / 'top.sv'
        self.cli('integrate', vendor, '-n', 'top', '-o', top, '--lint-config', '--package', pkg,
                 '-I', vendor_dir, '-y', vendor_dir, '-D', 'FEATURE=1')
        config = self.root / 'top.vlt'
        manifest = self.root / 'top.lint.f'
        self.assertNotIn(str(top), config.read_text())
        self.assertIn(str(vendor_dir/'*'), config.read_text())
        self.assertIn('-DFEATURE=1', manifest.read_text())
        self.lint(config, '-f', manifest)
        top.write_text(top.read_text().replace('endmodule\n', 'wire stray_top;\nendmodule\n'))
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top', str(config), '-f', str(manifest)], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('UNUSEDSIGNAL', result.stderr)
        self.assertIn(str(top), result.stderr)
        # An include directory containing the top must never introduce a waiver
        # glob that matches it. Paths with spaces must work in both collateral files.
        self.cli('update', top, '--files', vendor, '--lint-config', '--package', pkg, '-I', self.root, '-y', vendor_dir)
        self.assertNotIn(str(self.root/'*'), config.read_text())
        self.assertNotIn('"'+str(top)+'"', config.read_text())
