"""Batch A: unpacked buses, configured interfaces and real-module elaboration."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import test_integration as helpers
from test_parser import MODULE, SCRIPT

FIXTURES = Path(__file__).parent / 'fixtures/batch_a'
ROOT = Path(__file__).resolve().parents[4]


class BatchA(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def array_top(self, override=None, reverse=False):
        pkg = FIXTURES/'array_pkg.sv'
        socket = FIXTURES/'array_socket.sv'
        leaf = FIXTURES/'array_leaf.sv'
        specs = [{'module': 'array_socket', 'instance': 'u_socket'},
                 *[{'module': 'array_leaf', 'instance': f'u_leaf{i}'} for i in range(4 if override is None else 2)]]
        if override is not None:
            specs[0]['parameters'] = override
        if reverse:
            specs.reverse()  # An element driver must not determine the array declaration.
        data = {'instances': specs, 'mappings': {'u_socket.dev_o': 'req', 'u_socket.dev_i': 'rsp'},
                'templates': [{'regex': r'u_leaf(\d+)\.req_i', 'value': 'req[$1]'},
                              {'regex': r'u_leaf(\d+)\.rsp_o', 'value': 'rsp[$1]'}]}
        top = self.root/'top.sv'
        result = self.cli('integrate', socket, leaf, '--package', pkg, '--map', self.mapping(data), '-o', top)
        self.assertNotIn('width-mismatch', result.stderr)
        self.assertNotIn('width-unknown', result.stderr)
        self.assertNotIn('multiple-driver', result.stderr)
        n = 4 if override is None else 2
        text = top.read_text().split('// soc-integrate: ', 1)[1].split('\n', 1)[1]
        self.assertIn(f'array_pkg::req_t req [{n}];', text)
        self.assertIn(f'array_pkg::rsp_t rsp [{n}];', text)
        self.assertNotIn('NWD', text)
        self.assertNotIn('[N]', text)
        self.lint(pkg, socket, leaf, top)
        return top, pkg, socket, leaf

    def test_whole_unpacked_bus_and_elements_both_orders_lint(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                self.array_top(reverse=reverse)

    def test_int_string_bool_overrides_chains_and_refresh_lint(self):
        for n in (2, '2', '(1+1)'):
            for flag in (True, False):
                with self.subTest(n=n, flag=flag):
                    top, pkg, socket, leaf = self.array_top({'N': n, 'ExplicitErrs': flag})
                    code = top.read_text()
                    self.assertIn(f'.N({n})', code)
                    self.assertIn(".ExplicitErrs(1'b" + str(int(flag)) + ')', code)
                    self.assertIn('[1:0] u_socket_select_i' if flag else '[0:0] u_socket_select_i', code)
                    before = top.read_bytes()
                    self.cli('update', top, '--files', socket, leaf, '--package', pkg)
                    self.assertEqual(before, top.read_bytes())
                    self.lint(pkg, socket, leaf, top)

    def test_override_does_not_mutate_default_interface_and_passes_G(self):
        socket = MODULE.select_module(FIXTURES/'array_socket.sv', packages=[FIXTURES/'array_pkg.sv'])
        before = socket.metadata()
        inst = MODULE.default_instances([socket], {'instances': [{'module': socket.name, 'instance': 'u', 'parameters': {'N': 2}}]})
        calls, run = [], subprocess.run
        def record(command, **kwargs):
            calls.append(command)
            return run(command, **kwargs)
        with patch.object(MODULE.subprocess, 'run', side_effect=record):
            resolved = MODULE.resolve_instance(inst[0])
        self.assertEqual(socket.metadata(), before)
        self.assertEqual(resolved['module'].details['dev_o']['bits'], 18)
        self.assertEqual(resolved['module'].details['select_i']['resolved_width'], '[1:0]')
        self.assertTrue(any('-GN=2' in c for c in calls))
        self.assertIn('NWD', [p[0] for p in socket.localparams])
        self.assertNotIn('NWD', [p[0] for p in socket.params])

    def test_different_instance_localparam_widths_do_not_auto_share(self):
        dut = self.source('dut', """module dut #(parameter N=2,
localparam W=$clog2((N > 0) ? N+1 : 1))(input logic [W-1:0] select_i, output logic y);
assign y=^select_i;
endmodule""")
        data = {'instances': [{'module': 'dut', 'instance': 'u0', 'parameters': {'N': 2}},
                              {'module': 'dut', 'instance': 'u1', 'parameters': {'N': 4}}]}
        top = self.root/'top.sv'
        result = self.cli('integrate', dut, '--map', self.mapping(data), '-o', top)
        self.assertIn('auto-share-incompatible', result.stderr)
        self.assertNotIn('width-mismatch', result.stderr)
        self.assertIn('[1:0] u0_select_i', top.read_text())
        self.assertIn('[2:0] u1_select_i', top.read_text())
        self.lint(dut, top)

    def test_bad_override_types_and_unresolved_dimension_errors(self):
        for value in (None, [], {}, 2.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'int, str or bool'):
                    MODULE.parameter_value(value)
        dut = self.source('dut', 'module dut #(parameter N=4)(input [N-1:0] a); endmodule')
        m = MODULE.select_module(dut)
        inst = MODULE.default_instances([m], {'instances': [{'module': 'dut', 'instance': 'u_bad', 'parameters': {'N': 'missing'}}]})
        with self.assertRaisesRegex(ValueError, r'u_bad.*missing.*port a.*N-1'):
            MODULE.build_top(inst)
        with self.assertRaisesRegex(ValueError, 'unknown parameter overrides on u_bad'):
            MODULE.build_top([dict(inst[0], parameters={'ABSENT': 2})])

    def test_unpacked_element_width_and_packed_selection(self):
        sig = {'bus': {'bits': 64, 'detail': {'unpacked': '[2][0:3]'}}}
        self.assertEqual(MODULE.expression_width('bus[0]', sig), 32)
        self.assertEqual(MODULE.expression_width('bus[0][1]', sig), 8)
        self.assertEqual(MODULE.expression_width('bus[0][1][7:4]', sig), 4)
        self.assertEqual(MODULE.expression_width('bus', sig), 64)

    def test_multiple_wildcard_imports_disjoint_and_ambiguous(self):
        a = self.source('alpha', 'package alpha; typedef logic [6:0] a_t; endpackage')
        b = self.source('beta', 'package beta; typedef logic [8:0] b_t; endpackage')
        dut = self.source('dut', '''module dut import alpha::*; import beta::*;
(input a_t a, input b_t b, output logic y); assign y=(^a)^(^b); endmodule''')
        result = json.loads(self.cli('extract', dut, '--package', b, '--package', a).stdout)
        self.assertEqual([p['bits'] for p in result['ports']], [7, 9, 1])
        self.assertEqual(result['ports'][0]['declaration_type'], 'alpha::a_t')
        self.assertEqual(result['ports'][1]['declaration_type'], 'beta::b_t')
        top = self.root/'top.sv'
        self.cli('integrate', dut, '--package', a, '--package', b, '-o', top)
        self.lint(a, b, dut, top)
        b.write_text('package beta; typedef logic [8:0] b_t; typedef logic a_t; endpackage\n')
        error = self.cli('extract', dut, '--package', a, '--package', b, ok=False)
        self.assertIn('ambiguous type a_t: alpha::a_t, beta::a_t', error.stderr)
        self.assertIn('dut.a', error.stderr)

    def test_full_body_types_localparams_library_and_XML_fallback(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                with patch.object(MODULE, 'verilator_version', return_value=(5, 30) if legacy else (5, 32)):
                    m = MODULE.select_module(FIXTURES/'body_types.sv', library_dirs=[FIXTURES/'lib'])
                self.assertEqual(m.resolution, 'full')
                self.assertEqual([p[2] for p in m.ports], ['a', 'y'])
                self.assertEqual(m.details['y']['bits'], 8)
                self.assertEqual(m.details['y']['type'], 'local_word_t')
                self.assertEqual(m.details['y']['declaration_type'], 'logic')
                top = self.root/'top.sv'
                self.cli('integrate', FIXTURES/'body_types.sv', '-y', FIXTURES/'lib', '-o', top)
                self.lint('-y', FIXTURES/'lib', FIXTURES/'body_types.sv', top)

    def test_module_body_typedef_shadows_wildcard_import(self):
        pkg = self.source('alpha', 'package alpha; typedef logic word_t; endpackage')
        dut = self.source('dut', """module dut import alpha::*; (a, y);
input logic [7:0] a;
typedef logic [7:0] word_t;
output word_t y;
assign y=a;
endmodule""")
        m = MODULE.select_module(dut, packages=[pkg])
        self.assertEqual(m.details['y']['bits'], 8)
        top = self.root/'top.sv'
        self.cli('integrate', dut, '--package', pkg, '-o', top)
        self.assertIn('output logic [7:0] u_dut_y', top.read_text())
        self.lint(pkg, dut, top)

    def test_full_module_remaining_sources_and_real_error(self):
        body = FIXTURES/'body_types.sv'
        helper = FIXTURES/'lib/body_helper.sv'
        extracted = MODULE.extract_sources([body, helper])
        self.assertEqual(extracted[str(body)][0].details['y']['bits'], 8)
        error = self.cli('extract', body, ok=False)
        self.assertIn('full-module elaboration failed for module body_types', error.stderr)
        self.assertIn("Cannot find file containing module: 'body_helper'", error.stderr)
        self.assertNotIn('/soc-integrate-', error.stderr)

    def test_vendor_symbol_warning_config_keeps_top_fatal(self):
        vendor = self.root/'vendor'
        vendor.mkdir()
        pkg = vendor/'vendor_pkg.sv'
        pkg.write_text('package vendor_pkg; typedef struct packed { logic interrupt; } t; endpackage\n')
        dut = self.source('dut', 'module dut(input vendor_pkg::t a, output y); assign y=a.interrupt; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', dut, '--package', pkg, '--lint-config', '-o', top)
        self.lint(top.with_suffix('.vlt'), '-f', top.with_suffix('.lint.f'))
        self.assertIn('lint_off -rule SYMRSVDWORD -file', top.with_suffix('.vlt').read_text())
        top.write_text(top.read_text().replace('endmodule', 'wire top_warning;\nendmodule'))
        result = subprocess.run(['verilator', '--lint-only', '-Wall', '--top-module', 'top',
                                 str(top.with_suffix('.vlt')), '-f', str(top.with_suffix('.lint.f'))],
                                cwd=self.root, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('top_warning', result.stderr)

    @unittest.skipUnless(shutil.which('verilator'), 'Verilator unavailable')
    def test_real_cpu_common_ip_when_vendored(self):
        manifest = json.loads((FIXTURES/'real_sources.json').read_text())
        packages = [ROOT/p for p in manifest['packages']]
        sources = {n: ROOT/p for n, p in manifest['sources'].items()}
        if not all(p.exists() for p in packages + list(sources.values())):
            self.skipTest('vendored OpenTitan/Ibex package closure unavailable')
        prim = ROOT/'ip/digital/prim/de/rtl/src/hw/ip/prim/rtl'
        generic = prim.parent.parent/'prim_generic/rtl'
        libs = list(dict.fromkeys([prim, generic] + [p.parent for p in packages + list(sources.values())]))
        expected = {
            'ibex_top': (54, {'instr_addr_o': 32, 'data_addr_o': 32, 'irq_fast_i': 15,
                              'scramble_key_i': 128, 'scramble_nonce_i': 64, 'crash_dump_o': 160}),
            'rv_core_ibex': (41, {'corei_tl_h_o': 109, 'corei_tl_h_i': 66, 'crash_dump_o': 225}),
            'gpio': (14, {'tl_i': 109, 'tl_o': 66, 'intr_gpio_o': 32, 'sampled_straps_o': 33}),
            'tlul_adapter_sram': (22, {'tl_i': 109, 'tl_o': 66, 'addr_o': 12,
                                       'wdata_o': 32, 'wmask_o': 32, 'user_rsvd_o': 5}),
            'tlul_socket_1n': (7, {'tl_h_i': 109, 'tl_h_o': 66, 'tl_d_o': 436,
                                   'tl_d_i': 264, 'dev_select_i': 3}),
        }
        for name, path in sources.items():
            with self.subTest(module=name):
                m = MODULE.select_module(path, packages=packages, include_dirs=[prim, ROOT/'chip/top/de/rtl/vendor/opentitan/hw/dv/sv/dv_utils'], library_dirs=libs)
                count, widths = expected[name]
                self.assertEqual(len(m.ports), count)
                self.assertEqual(len(set(n for _, _, n in m.ports)), count)
                for port, bits in widths.items():
                    self.assertEqual(m.details[port]['bits'], bits, port)
                if name == 'ibex_top':
                    self.assertEqual(m.resolution, 'full')
                if name in ('gpio', 'rv_core_ibex'):
                    self.assertIn('::', m.details['sampled_straps_o' if name == 'gpio' else 'crash_dump_o']['declaration_type'])

