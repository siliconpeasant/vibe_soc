"""Batch 2: JSON/package dependencies, scalable refresh and connection diagnostics."""
import json
import shutil
import subprocess
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import test_integration as helpers
from test_parser import MODULE


class Batch2(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def packages(self):
        a = self.source('z_base_pkg', '''package z_base_pkg;
parameter int W=8;
typedef struct packed {logic [W-1:0] data; logic valid;} word_t;
endpackage''')
        b = self.source('a_use_pkg', '''package a_use_pkg;
import z_base_pkg::*;
typedef union packed {word_t word; logic [8:0] bits;} value_t;
endpackage''')
        dut = self.source('dut', '''module dut import a_use_pkg::*;
(input value_t x, input logic [z_base_pkg::W-1:0] a [2], output logic y);
assign y = (^x.bits) ^ (^a[0]) ^ (^a[1]);
endmodule''')
        return a, b, dut

    def test_json_preferred_width_probes_and_shuffled_packages_lint(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        a, b, dut = self.packages()
        result = json.loads(self.cli('extract', dut, '--package', b, '--package', a).stdout)
        self.assertEqual([p['bits'] for p in result['ports']], [9, 16, 1])
        self.assertEqual(result['ports'][1]['resolved_width'], '[7:0]')
        module = MODULE.extract_modules(dut)[0]
        calls, real_run = [], subprocess.run
        def run(command, **kwargs):
            calls.append(command)
            return real_run(command, **kwargs)
        with patch.object(MODULE, 'verilator_version', return_value=(5, 32)), patch.object(MODULE.subprocess, 'run', side_effect=run):
            MODULE.resolve_types(module, [a, b], [], [])
        self.assertTrue(any('--json-only' in c for c in calls))
        self.assertFalse(any('--xml-only' in c for c in calls))
        self.assertEqual(module.details['x']['bits'], 9)
        top = self.root/'top.sv'
        self.cli('integrate', dut, '-o', top, '--package', b, '--package', a, '--lint-config')
        manifest = top.with_suffix('.lint.f').read_text()
        self.assertLess(manifest.index(str(a)), manifest.index(str(b)))
        self.lint(top.with_suffix('.vlt'), '-f', top.with_suffix('.lint.f'))
        self.cli('update', top, '--package', a, '--package', b)
        self.lint(a, b, top)

    def test_ast_option_schema_and_old_version_fallbacks(self):
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        a, b, dut = self.packages()
        real_run = subprocess.run
        for scenario in ('option', 'schema', 'text', 'old'):
            calls = []
            module = MODULE.extract_modules(dut)[0]
            def run(command, **kwargs):
                calls.append(command)
                if '--json-only' in command:
                    if scenario == 'schema':
                        path = Path(command[command.index('--Mdir') + 1]); path.mkdir()
                        (path/'Vports.tree.json').write_text('{"unexpected":true}')
                        return subprocess.CompletedProcess(command, 0, '', '')
                    return subprocess.CompletedProcess(command, 1, '', '%Error: Invalid option: --json-only')
                if '--xml-only' in command and scenario == 'text':
                    return subprocess.CompletedProcess(command, 1, '', '%Error: Invalid option: --xml-only')
                return real_run(command, **kwargs)
            with self.subTest(scenario=scenario), patch.object(MODULE, 'verilator_version', return_value=(5, 20) if scenario == 'old' else (5, 32)), patch.object(MODULE.subprocess, 'run', side_effect=run):
                MODULE.resolve_types(module, [a, b], [], [])
                self.assertTrue(any('--xml-only' in c for c in calls))
                if scenario == 'text':
                    self.assertNotIn('bits', module.details['x'])
                    self.assertEqual(module.details['x']['type'], 'value_t')
                else:
                    self.assertEqual(module.details['x']['bits'], 9)
                if scenario == 'old':
                    self.assertFalse(any('--json-only' in c for c in calls))
        MODULE.verilator_version.cache_clear()
        with patch.object(MODULE.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'Verilator 5.032 test', '')):
            self.assertEqual(MODULE.verilator_version(), (5, 32))
        MODULE.verilator_version.cache_clear()

    def test_package_cycles_missing_and_real_included_locations(self):
        a = self.source('a', 'package alpha;\nparameter N=beta::N;\nendpackage')
        b = self.source('b', 'package beta;\nparameter N=alpha::N;\nendpackage')
        dut = self.source('dut', 'module dut(input logic x, output logic y); assign y=x; endmodule')
        result = self.cli('extract', dut, '--package', b, '--package', a, ok=False)
        self.assertIn('dependency cycle', result.stderr)
        self.assertRegex(result.stderr, r'[ab]\.sv:2:')
        inc = self.root/'missing.svh'; inc.write_text('parameter N=missing_pkg::N;\n')
        a.write_text('package alpha;\n`include "missing.svh"\nendpackage\n')
        result = self.cli('extract', dut, '--package', a, ok=False)
        self.assertIn(f'{inc}:1: missing package missing_pkg', result.stderr)
        a.write_text('package alpha; parameter N=1; endpackage\n')
        dut.write_text('module dut(\ninput alpha::missing_t x, output logic y); assign y=|x; endmodule\n')
        result = self.cli('extract', dut, '--package', a, ok=False)
        self.assertIn(f'{dut}:2:', result.stderr)
        self.assertNotIn('/soc-integrate-', result.stderr)
        # Header diagnostics retain included port locations as well.
        inc.write_text('input alpha::missing_t x,\n')
        dut.write_text('module dut(\n`include "missing.svh"\noutput logic y); assign y=|x; endmodule\n')
        result = self.cli('extract', dut, '--package', a, ok=False)
        self.assertIn(f'{inc}:1:', result.stderr)
        a.write_text('package alpha;\nparameter N=beta::N;\nendpackage\npackage beta;\nparameter N=alpha::N;\nendpackage\n')
        result = self.cli('extract', dut, '--package', a, ok=False)
        self.assertIn('package dependency cycle', result.stderr)
        self.assertRegex(result.stderr, r'a\.sv:(2|5):')

    def test_packages_comments_strings_inactive_code_and_multiple_declarations(self):
        a = self.source('alpha', '''package alpha; parameter N=3; endpackage
`include "beta.svh"''')
        (self.root/'beta.svh').write_text('package beta; parameter N=alpha::N; endpackage\n')
        b = self.source('gamma', '''package gamma;
// absent::unused
parameter string S="absent::unused";
`ifdef ABSENT
parameter N=absent::unused;
`else
parameter N=beta::N;
`endif
endpackage''')
        dut = self.source('dut', 'module dut(input [gamma::N-1:0] a, output y); assign y=(|a) ^ (gamma::S == "absent::unused"); endmodule')
        self.cli('integrate', dut, '-o', self.root/'top.sv', '--package', b, '--package', a)
        self.lint(a, b, self.root/'top.sv')

    def test_1000_instances_compact_metadata_and_fast_refresh(self):
        # Same 22-port workload as the review generator. A little timing margin
        # avoids scheduler noise; the external RUN records unprofiled timings.
        ports = ['input logic clk_i', 'input logic rst_ni'] + [f'input logic [31:0] in{i}_m0_i' for i in range(10)] + [f'output logic [31:0] out{i}_m0_o' for i in range(10)]
        logic = ' '.join(f'assign out{i}_m0_o = in{i}_m0_i ^ {{32{{clk_i & rst_ni}}}};' for i in range(10))
        dut = self.source('m0', 'module m0('+','.join(ports)+'); '+logic+' endmodule')
        mapping = self.mapping({'instances': [{'module': 'm0', 'instance': f'u{i}'} for i in range(1000)],
                                'templates': [{'regex': r'u(\d+)\.(\w+)', 'value': 'n$1_$2'}]})
        top = self.root/'top.sv'
        commands = [('integrate', dut, '--map', mapping, '-o', top), ('update', top), ('diff', top)]
        for command in commands:
            start = time.perf_counter()
            self.cli(*command)
            self.assertLess(time.perf_counter() - start, 2.5, command[0])
        raw = top.read_text().splitlines()[1]
        self.assertLess(len(raw), 100_000)
        meta = json.loads(raw.split(': ', 1)[1])
        self.assertEqual(meta['version'], 2)
        self.assertEqual(list(meta['modules']), ['m0'])
        self.assertEqual(len(meta['instances']), 1000)
        self.assertNotIn('ports', meta['instances']['u0'])
        self.assertNotIn(str(self.root), raw)
        first = top.read_bytes(); self.cli('update', top)
        self.assertEqual(first, top.read_bytes())
        self.lint(dut, top)

    def test_metadata_portability_relative_paths_legacy_and_wrapper(self):
        trees = []
        for dirname in ('one', 'two'):
            directory = self.root/dirname; directory.mkdir()
            dut = directory/'dut.sv'; dut.write_text('module dut(input a, output y); assign y=a; endmodule\n')
            top = directory/'top.sv'
            self.cli('integrate', dut, '-o', top)
            trees.append(top)
        self.assertEqual(trees[0].read_bytes(), trees[1].read_bytes())
        moved = self.root/'moved'; shutil.copytree(trees[0].parent, moved)
        self.cli('update', moved/'top.sv')
        self.assertEqual(trees[0].read_bytes(), (moved/'top.sv').read_bytes())
        self.lint(moved/'dut.sv', moved/'top.sv')
        # Construct the pre-v2 full-instance layout with absolute paths.
        legacy = MODULE.parse_top(moved/'top.sv')[2]
        legacy.pop('modules'); legacy['version'] = 1
        lines = (moved/'top.sv').read_text().splitlines()
        lines[1] = '// soc-integrate: '+json.dumps(legacy)
        (moved/'top.sv').write_text('\n'.join(lines)+'\n')
        self.cli('update', moved/'top.sv')
        self.assertEqual(trees[0].read_bytes(), (moved/'top.sv').read_bytes())
        wrapper = moved/'wrapper.sv'
        self.cli('wrap', moved/'dut.sv', '-n', 'wrapper', '-o', wrapper)
        self.cli('update', wrapper)
        self.lint(moved/'dut.sv', wrapper, top='wrapper')

    def test_rename_suggestions_stale_maps_and_removed_internal_input(self):
        a = self.source('a', 'module a(input x, output [7:0] old); assign old={8{x}}; endmodule')
        b = self.source('b', 'module b(input [7:0] old, output y); assign y=|old; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', a, b, '-o', top)
        before = top.read_bytes()
        a.write_text(a.read_text().replace('old', 'fresh'))
        for cmd in ('diff', 'update'):
            result = self.cli(cmd, top, '--strict', ok=False)
            self.assertIn('[REN?] u_a.old -> u_a.fresh', result.stdout)
            self.assertIn('"u_a.fresh": "old"', result.stdout)
            self.assertIn('former internal net old would become a new top-level input', result.stderr)
            self.assertEqual(before, top.read_bytes())
        mapping = self.mapping({'mappings': {'u_a.fresh': 'old', 'u_a.gone': 'x', 'missing.a': 'x'}})
        result = self.cli('update', top, '--map', mapping)
        self.assertIn('[stale-port-map]: u_a.gone', result.stderr)
        self.assertIn('[stale-port-map]: missing.a', result.stderr)
        self.assertIn('.fresh(old)', top.read_text())
        self.assertNotIn('removed-port-exposes-net', result.stderr)
        result = self.cli('diff', top)
        self.assertIn('[stale-port-map]', result.stderr)
        self.lint(a, b, top)

    def test_removed_sink_exposes_output_and_ambiguous_rename_is_not_guessed(self):
        a = self.source('a', 'module a(input x, output [7:0] q); assign q={8{x}}; endmodule')
        b = self.source('b', 'module b(input [7:0] q, output y); assign y=|q; endmodule')
        top = self.root/'top.sv'; self.cli('integrate', a, b, '-o', top)
        b.write_text('module b(input x, output y); assign y=x; endmodule\n')
        result = self.cli('diff', top)
        self.assertNotIn('[REN?]', result.stdout)  # width differs
        self.assertIn('new top-level output', result.stderr)
        b.write_text('module b(input [7:0] n, input [7:0] m, output y); assign y=|n ^ |m; endmodule\n')
        self.assertNotIn('[REN?]', self.cli('diff', top).stdout)

    def test_snapshot_rename_reports_map_key_without_inventing_connection(self):
        dut = self.source('dut', 'module dut(input [7:0] old, output y); assign y=|old; endmodule')
        self.cli('snapshot', dut, '-f', 'json')
        dut.write_text(dut.read_text().replace('old', 'fresh'))
        result = self.cli('diff', dut, self.root/'dut_ports.json')
        self.assertIn('[REN?] dut.old -> dut.fresh', result.stdout)
        self.assertIn('"dut.fresh": "<former connection>"', result.stdout)
        self.assertIn('snapshot has no connections', result.stdout)

    def test_fast_declaration_ownership_preserves_trailing_comments(self):
        a = self.source('a', 'module a(input x, output q); assign q=x; endmodule')
        b = self.source('b', 'module b(input q, output y); assign y=q; endmodule')
        top = self.root/'top.sv'; self.cli('integrate', a, b, '-o', top)
        top.write_text(top.read_text().replace('    wire q;', '    wire q; // user explanation'))
        self.cli('update', top)
        self.assertEqual(top.read_text().count('    wire q;'), 1)
        self.assertIn('// user explanation', top.read_text())
        first = top.read_bytes(); self.cli('update', top)
        self.assertEqual(first, top.read_bytes())
        self.lint(a, b, top)

    def test_interface_array_unused_and_undriven_elements_all_workflows(self):
        interface = self.source('bus_if', '''interface bus_if;
logic data;
modport src(output data), sink(input data);
endinterface''')
        src = self.source('src', "module src(input x, bus_if.src m); assign m.data=x; endmodule")
        sink = self.source('sink', 'module sink(bus_if.sink s [4], output y); assign y=s[0].data ^ s[1].data ^ s[2].data ^ s[3].data; endmodule')
        data = {'instances': [{'module': 'src', 'instance': f'u{i}'} for i in range(3)],
                'templates': [{'regex': r'u(\d+)\.m', 'value': 'bus[$1]'}],
                'interfaces': {'bus': {'type': 'bus_if', 'unpacked': '[4]'}}}
        mapping = self.mapping(data); top = self.root/'top.sv'
        result = self.cli('integrate', interface, src, '-o', top, '--map', mapping)
        self.assertIn('[interface-element-unconnected]: bus[3]', result.stderr)
        for cmd in ('check', 'update'):
            self.assertIn('[interface-element-unconnected]: bus[3]', self.cli(cmd, top).stderr)
        # Add a whole-array input modport. Element 3 is connected, but undriven.
        data['instances'].append({'module': 'sink', 'instance': 'u_sink'})
        data['mappings'] = {'u_sink.s': 'bus'}; mapping.write_text(json.dumps(data))
        top.unlink()
        result = self.cli('integrate', interface, src, sink, '-o', top, '--map', mapping)
        self.assertIn('[interface-element-undriven]: bus[3]', result.stderr)
        for cmd in ('check', 'update'):
            self.assertIn('[interface-element-undriven]: bus[3]', self.cli(cmd, top).stderr)
        before = top.read_bytes()
        self.cli('update', top, '--strict', ok=False)
        self.assertEqual(before, top.read_bytes())
        # Explicitly drive the remaining element in a protected user region;
        # coverage checks remain conservative about opaque custom logic.
        top.write_text(top.read_text().replace('endmodule', '// soc-integrate:user begin\nassign bus[3].data=src_input;\n// soc-integrate:user end\nendmodule').replace('src_input', 'x'))
        self.lint(interface, src, sink, top)

    def test_interface_whole_source_and_nonzero_descending_bounds(self):
        interface = self.source('bus_if', 'interface bus_if; logic d; modport src(output d); endinterface')
        dut = self.source('dut', 'module dut(input a, bus_if.src s); assign s.d=a; endmodule')
        mapping = self.mapping({'mappings': {'dut.s': 'bus[5]'}, 'interfaces': {'bus': {'unpacked': '[5:3]'}}})
        result = self.cli('integrate', interface, dut, '-o', self.root/'top.sv', '--map', mapping)
        self.assertIn('bus[3:4]', result.stderr)
        self.assertNotIn('undriven', result.stderr)
        whole = self.source('whole', "module whole(input a, bus_if.src s [4]); for(genvar i=0;i<4;i++) begin : gen_drive assign s[i].d=a; end endmodule")
        mapping.write_text(json.dumps({'mappings': {'whole.s': 'bus'}}))
        (self.root/'top.sv').unlink()
        result = self.cli('integrate', interface, whole, '-o', self.root/'top.sv', '--map', mapping)
        self.assertNotIn('interface-element', result.stderr)
        # Consume each element so -Wall also checks the generated top.
        top = self.root/'top.sv'
        top.write_text(top.read_text().replace('module top (', 'module top (\n    output y,').replace('endmodule', '// soc-integrate:user begin\nassign y=bus[0].d ^ bus[1].d ^ bus[2].d ^ bus[3].d;\n// soc-integrate:user end\nendmodule'))
        self.lint(interface, whole, top)


if __name__ == '__main__':
    unittest.main()
