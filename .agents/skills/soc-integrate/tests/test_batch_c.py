"""Batch C acceptance fixes: constants, hand-written glue, scoped vendor lint."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

import test_integration as helpers
from test_parser import MODULE

FIXTURES = Path(__file__).parent / 'fixtures/batch_c'


class BatchC(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def test_package_enum_constant_chip_refresh_and_fatal_lint(self):
        pkg, sink = FIXTURES/'control_pkg.sv', FIXTURES/'control_sink.sv'
        data = dict(chip=True, pads=['u_control_sink.enabled_o'],
                    mappings={'u_control_sink.enable_i': 'control_pkg::Enabled'})
        top = self.root/'top.sv'
        result = self.cli('integrate', sink, '--package', pkg, '--map', self.mapping(data), '-o', top)
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertIn('.enable_i(control_pkg::Enabled)', top.read_text())
        self.lint(pkg, sink, top)
        before = top.read_bytes()
        for op in ('update', 'check', 'diff'):
            self.cli(op, top, '--files', sink, '--package', pkg, '--strict')
        self.assertEqual(before, top.read_bytes())

    def test_qualified_constants_keep_width_validation_and_reject_nonconstants(self):
        pkg = self.source('control_pkg', (FIXTURES/'control_pkg.sv').read_text().replace(
            'endpackage', 'logic [3:0] runtime_value;\nendpackage'))
        sink = self.source('sink', 'module sink(input [3:0] a, output y); assign y=^a; endmodule')
        top = self.root/'top.sv'
        for value, expected in [('Wide', 'width mismatch'), ('Absent', 'Absent'),
                                ('runtime_value', 'constant')]:
            with self.subTest(value=value):
                result = self.cli('integrate', sink, '--package', pkg, '--map',
                                  self.mapping({'mappings': {'sink.a': 'control_pkg::' + value}}),
                                  '-o', top, '--strict', ok=False)
                self.assertIn(expected, result.stderr)
                self.assertFalse(top.exists())
        result = self.cli('integrate', sink, '--package', pkg, '--map',
                          self.mapping({'mappings': {'sink.y': 'control_pkg::Enabled'}}),
                          '-o', top, ok=False)
        self.assertIn('constant on output', result.stderr)

    def shell(self, user):
        top = self.root/'top.sv'
        top.write_text(MODULE.build_top([], 'top', top_file=top)[0].replace(
            'endmodule', '// soc-integrate:user begin\n' + user + '\n// soc-integrate:user end\nendmodule'))
        return top

    def glue_data(self):
        return dict(chip=True, pads=['clk_i', 'rst_ni', 'u_src.address_i', 'u_src.request_i', 'u_sink.response_o'],
                    instances=[dict(module='glue_source', instance='u_src'), dict(module='glue_sink', instance='u_sink')],
                    mappings={'u_src.address_o': 'address', 'u_src.request_o': 'request',
                              'u_sink.select_i': 'select', 'u_sink.valid_i': 'valid', 'u_sink.irq_i': 'irq'},
                    clocks={'main': {'net': 'clk_i'}}, resets={'main': {'net': 'rst_ni'}},
                    irq={'target': 'irq_bus', 'width': 2, 'sources': ['u_src.intr_*']})

    def glue(self):
        return '''wire [1:0] select;
logic valid;
wire irq;
assign select = {^address[7:4], ^address[3:0]};
assign irq = |irq_bus;
always @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
        valid <= 1'b0;
    end else begin
        valid <= request;
    end
end'''

    def test_user_decode_handshake_irq_graph_chip_refresh_and_fatal_lint(self):
        user = self.glue()
        top = self.shell(user)
        sources = [FIXTURES/'glue_source.sv', FIXTURES/'glue_sink.sv']
        result = self.cli('integrate', *sources, '--map', self.mapping(self.glue_data()), '-o', top)
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertEqual(len(MODULE.select_module(top).ports), 5)
        self.lint(*sources, top)
        before = top.read_bytes()
        for op in ('update', 'check', 'diff', 'update'):
            result = self.cli(op, top, '--files', *sources, '--strict')
            self.assertIn('Checks: 0 warning(s)', result.stderr)
            self.assertIn(user, top.read_text())
            self.assertEqual(before, top.read_bytes())
        self.lint(*sources, top)

    def test_user_declarations_comments_and_comparisons_do_not_supply_drivers(self):
        for user in [self.glue().replace('assign select = {^address[7:4], ^address[3:0]};', '// assign select = {^address[7:4], ^address[3:0]};'),
                     self.glue().replace('assign select = {^address[7:4], ^address[3:0]};', 'wire comparison = (select <= address[1:0]);'),
                     self.glue().replace('assign select = {^address[7:4], ^address[3:0]};', 'wire comparison; assign comparison = (select <= address[1:0]);'),
                     self.glue().replace('assign select = {^address[7:4], ^address[3:0]};', 'if (select <= 2) begin end')]:
            top = self.shell(user)
            before = top.read_bytes()
            result = self.cli('integrate', FIXTURES/'glue_source.sv', FIXTURES/'glue_sink.sv',
                              '--map', self.mapping(self.glue_data()), '-o', top, ok=False)
            self.assertIn('u_sink.select_i has no driver', result.stderr)
            self.assertEqual(before, top.read_bytes())

    def test_user_partial_assignments_and_overlapping_child_driver(self):
        for user, expected in [(self.glue().replace('select = {^address[7:4], ^address[3:0]}', "select[0] = address[7]"),
                                 'u_sink.select_i has no driver'),
                                (self.glue() + "\nassign request = 1'b1;", 'multiple-driver')]:
            top = self.shell(user)
            result = self.cli('integrate', FIXTURES/'glue_source.sv', FIXTURES/'glue_sink.sv',
                              '--map', self.mapping(self.glue_data()), '-o', top, ok=False)
            self.assertIn(expected, result.stderr)
        user = self.glue().replace('assign select = {^address[7:4], ^address[3:0]};',
                                  'assign select[0] = ^address[3:0];\nassign select[1] = ^address[7:4];')
        top = self.shell(user)
        self.cli('integrate', FIXTURES/'glue_source.sv', FIXTURES/'glue_sink.sv',
                 '--map', self.mapping(self.glue_data()), '-o', top, '--strict')
        self.lint(FIXTURES/'glue_source.sv', FIXTURES/'glue_sink.sv', top)

    def test_user_graph_ignores_scoped_logic_strings_and_member_lvalues(self):
        top = SimpleNamespace(user_regions=['''// assign a = 1'b1;
function f; a = 1'b1; endfunction
wire dummy = "a = b";
assign thing.a = b;
'''], unmanaged_text='')
        ref = dict(width='', bits=1, detail={'type': 'wire', 'unpacked': ''})
        rows = MODULE.user_connections(top, {'a': ref, 'b': ref})
        self.assertFalse(any(r['signal'] == 'a' and r['direction'] == 'output' for r in rows))

    def test_vendor_multidriven_scoped_and_generated_top_still_fatal(self):
        vendor = self.root/'vendor'
        vendor.mkdir()
        source = vendor/'vendor_arbiter.sv'
        shutil.copyfile(FIXTURES/'vendor_arbiter.sv', source)
        top = self.root/'top.sv'
        self.cli('integrate', source, '-o', top, '--lint-config')
        config = top.with_suffix('.vlt')
        self.assertIn('lint_off -rule MULTIDRIVEN -file', config.read_text())
        self.assertNotIn(str(top), config.read_text())
        self.lint(config, '-f', top.with_suffix('.lint.f'))
        # The same warning originating in the generated top must remain fatal.
        top.write_text(top.read_text().replace('endmodule', '''logic [1:0] top_tree;
assign top_tree[0] = u_vendor_arbiter_a[0];
always_comb begin
    top_tree[1] = u_vendor_arbiter_a[1];
    top_tree[0] = ^u_vendor_arbiter_a;
end
wire unused_top_result = ^top_tree;
endmodule'''))
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top', str(config),
                                 '-f', str(top.with_suffix('.lint.f'))], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex(result.stderr, r'%Warning-MULTIDRIVEN: .*top.sv:')
