"""Batch B: chip completeness, deterministic IRQ wiring and supplied domains."""
import copy
import json
import unittest
from pathlib import Path

import test_integration as helpers
import test_batch_a
from test_parser import MODULE

FIXTURES = Path(__file__).parent / 'fixtures/batch_b'


class BatchB(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def pad_data(self):
        return {'chip': True, 'instances': [{'module': 'pad_unit', 'instance': 'u_uart'}],
                'pads': ['clk_main_i', 'rst_main_ni', 'u_uart.pad_*',
                         {'name': 'uart_tx_o', 'from': 'u_uart.tx_o'}],
                'clocks': {'main': {'net': 'clk_main_i'}},
                'resets': {'main': {'net': 'rst_main_ni'}},
                'mappings': {'u_uart.enable_i': "1'b0", 'u_uart.config_i': "{N{1'b0}}",
                             'u_uart.intr_o': None, 'u_uart.status_o': None}}

    def integrate_pad(self, data=None, *args, ok=True):
        data = self.pad_data() if data is None else data
        top = self.root/'top.sv'
        result = self.cli('integrate', FIXTURES/'pad_unit.sv', '--map', self.mapping(data),
                          '-o', top, *args, ok=ok)
        return top, result

    def test_chip_globs_rename_replication_ties_opens_and_refresh_lint(self):
        top, result = self.integrate_pad()
        self.assertNotIn('width-unknown', result.stderr)
        self.assertEqual([n for _, _, n in MODULE.select_module(top).ports],
                         ['clk_main_i', 'rst_main_ni', 'u_uart_pad_i', 'uart_tx_o'])
        self.assertIn(".config_i({2{1'b0}})", top.read_text())
        self.assertIn('.tx_o(uart_tx_o)', top.read_text())
        self.assertNotIn('rst_synchronizer', top.read_text())
        self.lint(FIXTURES/'pad_unit.sv', top)
        before = top.read_bytes()
        self.cli('update', top, '--files', FIXTURES/'pad_unit.sv')
        self.assertEqual(top.read_bytes(), before)
        self.cli('check', top, '--files', FIXTURES/'pad_unit.sv')

    def test_cli_chip_and_top_ports_alias_and_net_glob(self):
        data = self.pad_data()
        del data['chip']
        data['top_ports'] = ['clk_*', 'rst_*', 'u_uart_pad_i', 'u_uart_tx_o']
        del data['pads']
        top, _ = self.integrate_pad(data, '--chip')
        self.assertEqual(len(MODULE.select_module(top).ports), 4)
        self.lint(FIXTURES/'pad_unit.sv', top)

    def test_all_untied_errors_include_direction_type_and_no_outputs(self):
        data = {'chip': True, 'instances': [{'module': 'pad_unit', 'instance': 'u_uart'}]}
        top, result = self.integrate_pad(data, '--track', '--csv', '--lint-config', ok=False)
        for direction, _, port in MODULE.select_module(FIXTURES/'pad_unit.sv').ports:
            self.assertRegex(result.stderr, rf'u_uart\.{port}: {direction} (wire|reg)')
        self.assertIn('chip-untied', result.stderr)
        self.assertEqual(list(self.root.glob('top*')), [])
        self.assertFalse(top.exists())

    def test_failures_leave_existing_outputs_untouched(self):
        top, _ = self.integrate_pad()
        before = top.read_bytes()
        data = self.pad_data()
        del data['mappings']['u_uart.enable_i']
        _, result = self.integrate_pad(data, '--irq-json', self.root/'irqs.json', ok=False)
        self.assertIn('u_uart.enable_i', result.stderr)
        self.assertEqual(top.read_bytes(), before)
        self.assertFalse((self.root/'irqs.json').exists())

    def test_pad_unmatched_rename_collision_and_invalid_pads(self):
        for change, expected in [(['no_such.*'], 'pad-unmatched'),
                                 ([{'name': 'u_uart_pad_i', 'from': 'u_uart.tx_o'}], 'conflicting pad renames'),
                                 ([{'name': 'bad-name', 'from': 'u_uart.tx_o'}], 'invalid pad name'),
                                 ([{'name': 'merged', 'from': 'u_uart.*'}], 'whole net')]:
            data = self.pad_data()
            data['pads'] += change
            with self.subTest(change=change):
                _, result = self.integrate_pad(data, ok=False)
                self.assertIn(expected, result.stderr)
                self.assertFalse((self.root/'top.sv').exists())

    def test_null_input_not_a_tie_and_constant_output_is_error(self):
        for port, value, expected in [('enable_i', None, 'undriven-input'),
                                      ('status_o', "1'b0", 'constant on output')]:
            data = self.pad_data()
            data['mappings']['u_uart.' + port] = value
            _, result = self.integrate_pad(data, ok=False)
            self.assertIn(expected, result.stderr)

    def test_instance_prefixes_for_one_and_repeated_modules_lint(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        for instances in ([{'module': 'dut', 'instance': 'u_io'}],
                          [{'module': 'dut', 'instance': n} for n in ('u_io', 'u_io2')]):
            top = self.root/'top.sv'
            self.cli('integrate', dut, '-o', top, '--map', self.mapping({'instances': instances}))
            ports = [n for _, _, n in MODULE.select_module(top).ports]
            self.assertIn('u_io_y', ports)
            self.assertEqual(len(ports), len(set(ports)))
            if len(instances) == 1:
                self.assertIn('u_io_a', ports)
            else:
                self.assertIn('u_io2_y', ports)
            self.lint(dut, top)

    def test_completeness_check_uses_actual_internal_nets_all_modes(self):
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', dut, '-o', top)
        top.write_text(top.read_text().replace('    input wire u_dut_a,\n', '')
                       .replace('    output wire u_dut_y', '    input wire unused_pad')
                       .replace(');\n    dut', ');\n    wire u_dut_a;\n    wire u_dut_y;\n    dut'))
        result = self.cli('check', top, '--files', dut, '--strict', ok=False)
        self.assertIn('[undriven-input]: u_dut.a', result.stderr)
        self.assertIn('[unused-output]: u_dut.y', result.stderr)
        data = {'chip': True, 'pads': ['miss.*']}
        result = self.cli('check', top, '--files', dut, '--map', self.mapping(data), ok=False)
        self.assertIn('pad-unmatched', result.stderr)
        self.assertIn('chip-unapproved-pad', result.stderr)

    def test_check_does_not_apply_pad_renames_to_actual_wiring(self):
        top, _ = self.integrate_pad()
        top.write_text(top.read_text().replace('.tx_o(uart_tx_o)', '.tx_o(broken_tx)')
                       .replace(');\n    pad_unit', ');\n    wire broken_tx;\n    pad_unit'))
        result = self.cli('check', top, '--files', FIXTURES/'pad_unit.sv', ok=False)
        self.assertIn('u_uart.tx_o drives no consumer for broken_tx', result.stderr)

    def test_chip_expression_consumers_participate_in_graph_and_cdc(self):
        a = self.source('a', "module a(output [1:0] data_o); assign data_o=2'b10; endmodule")
        b = self.source('b', 'module b(input [1:0] data_i, output y); assign y=^data_i; endmodule')
        data = {'chip': True, 'pads': ['u_b.y'],
                'mappings': {'u_a.data_o': 'data', 'u_b.data_i': '{data[0], data[1]}'},
                'domains': {'u_a': 'fast', 'u_b': 'slow'}}
        top = self.root/'top.sv'
        result = self.cli('integrate', a, b, '--map', self.mapping(data), '-o', top)
        self.assertNotIn('unused-output', result.stderr)
        self.assertNotIn('undriven-input', result.stderr)
        self.assertIn('u_a.data_o (fast) -> u_b.data_i (slow)', result.stderr)
        self.lint(a, b, top)

    def test_chip_multiple_driver_reports_endpoints_and_no_write(self):
        dut = self.source('dut', 'module dut(output y); assign y=1\'b0; endmodule')
        data = {'chip': True, 'pads': ['pad'],
                'instances': [{'module': 'dut', 'instance': n} for n in ('u0', 'u1')],
                'mappings': {'u0.y': 'pad', 'u1.y': 'pad'}}
        top = self.root/'top.sv'
        result = self.cli('integrate', dut, '-o', top, '--map', self.mapping(data), ok=False)
        self.assertIn('multiple drivers: u0.y, u1.y', result.stderr)
        self.assertFalse(top.exists())

    def test_chip_connected_by_sharing_allowed_and_partial_drive_rejected(self):
        a = self.source('a', 'module a(output q); assign q=1\'b0; endmodule')
        b = self.source('b', 'module b(input q, output y); assign y=q; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', a, b, '-o', top, '--chip', '--map', self.mapping({'pads': ['u_b.y']}))
        self.assertEqual([n for _, _, n in MODULE.select_module(top).ports], ['u_b_y'])
        self.lint(a, b, top)
        wide = self.source('wide', 'module wide(input [1:0] q, output y); assign y=^q; endmodule')
        result = self.cli('integrate', a, wide, '-o', self.root/'bad.sv', '--chip',
                          '--map', self.mapping({'mappings': {'u_a.q': 'q[0]', 'u_wide.q': 'q'},
                                                'pads': ['u_wide.y']}), ok=False)
        self.assertIn('u_wide.q has no driver', result.stderr)

    def irq_data(self, net=False):
        return {'chip': True, 'instances': [{'module': 'irq_source', 'instance': 'u_b'},
                                            {'module': 'irq_source', 'instance': 'u_a'},
                                            {'module': 'irq_sink', 'instance': 'u_plic'}],
                'clocks': {'main': {'net': 'clk', 'top': True}},
                'resets': {'main': {'net': 'rst_n', 'top': True}},
                'pads': ['u_plic.irq_o'],
                'mappings': {'u_b.event_i': "2'b10", 'u_a.event_i': "'0",
                             **({'u_plic.intr_src_i': 'irq_bus'} if net else {})},
                'irq': {'target': 'irq_bus' if net else 'u_plic.intr_src_i',
                        'sources': ['u_a.intr_b_o', 'u_*.intr_a_o', 'u_b.intr_b_o'], 'reserve_zero': True}}

    def integrate_irq(self, data=None, *args, ok=True):
        top = self.root/'top.sv'
        result = self.cli('integrate', FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv',
                          '-o', top, '--map', self.mapping(self.irq_data() if data is None else data), *args, ok=ok)
        return top, result

    def test_irq_order_globs_multibit_reserve_padding_exports_refresh_lint(self):
        table, header = self.root/'irqs.json', self.root/'irqs.h'
        top, result = self.integrate_irq(None, '--irq-json', table, '--irq-header', header, '--strict')
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        entries = json.loads(table.read_text())
        self.assertEqual(entries['width'], 8)
        self.assertEqual(entries['count'], 7)
        self.assertEqual([e['source'] for e in entries['irqs']],
                         ['u_a.intr_b_o[1]', 'u_a.intr_b_o[2]', 'u_b.intr_a_o',
                          'u_a.intr_a_o', 'u_b.intr_b_o[1]', 'u_b.intr_b_o[2]'])
        self.assertEqual([e['index'] for e in entries['irqs']], list(range(1, 7)))
        self.assertTrue(all(e['module'] == 'irq_source' for e in entries['irqs']))
        self.assertIn('#define TOP_IRQ_U_A_INTR_B_O_1 1', header.read_text())
        self.assertIn('#define TOP_IRQ_U_B_INTR_A_O 3', header.read_text())
        self.assertIn('#define TOP_IRQ_COUNT 7', header.read_text())
        self.assertIn("assign u_plic_intr_src_i = {1'b0, u_b_intr_b_o[2], u_b_intr_b_o[1], u_a_intr_a_o, u_b_intr_a_o, u_a_intr_b_o[2], u_a_intr_b_o[1], 1'b0};", top.read_text())
        self.lint(FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv', top)
        before = top.read_bytes()
        self.cli('update', top, '--files', FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv', '--strict')
        self.assertEqual(before, top.read_bytes())
        self.cli('check', top, '--files', FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv', '--strict')
        self.lint(FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv', top)

    def test_irq_net_target_no_reservation_and_opt_in_only(self):
        data = self.irq_data(net=True)
        data['irq']['reserve_zero'] = False
        top, _ = self.integrate_irq(data, '--strict')
        self.assertIn("assign irq_bus = {2'b0,", top.read_text())
        self.assertEqual(sorted(p.name for p in self.root.glob('top*')), ['top.sv'])
        self.lint(FIXTURES/'irq_source.sv', FIXTURES/'irq_sink.sv', top)

    def test_standalone_irq_net_pad_and_unused_net_error(self):
        data = self.irq_data()
        data['instances'] = [data['instances'][1]]
        data['mappings'] = {'u_a.event_i': "'0"}
        data['irq'] = {'target': 'irqs', 'sources': ['u_a.intr_*_o']}
        data['pads'] = ['irqs']
        top, _ = self.integrate_irq(data, '--strict')
        self.assertIn('output wire [2:0] irqs', top.read_text())
        self.lint(FIXTURES/'irq_source.sv', top)
        data['pads'] = []
        _, result = self.integrate_irq(data, ok=False)
        self.assertIn('drives no consumer', result.stderr)

    def test_array_elements_cover_full_net_and_missing_element_is_error(self):
        top, pkg, socket, leaf = test_batch_a.BatchA.array_top(self)
        result = self.cli('check', top, '--files', socket, leaf, '--package', pkg)
        self.assertNotIn('undriven-input', result.stderr)
        self.assertNotIn('multiple-driver', result.stderr)
        data = json.loads((self.root/'map.json').read_text())
        data.update(chip=True, pads=['u_socket.host_*', 'u_socket.select_i'])
        self.cli('integrate', socket, leaf, '-o', top, '--map', self.mapping(data), '--package', pkg)
        self.lint(pkg, socket, leaf, top)
        data['instances'].pop()
        result = self.cli('integrate', socket, leaf, '-o', self.root/'bad.sv', '--map', self.mapping(data),
                          '--package', pkg, ok=False)
        self.assertIn('u_socket.dev_i has no driver', result.stderr)

    def test_irq_target_too_small_bad_sources_duplicates_and_width(self):
        for patch, expected in [({'width': 9}, 'exceeds target'), ({'width': 2}, 'too small'),
                                ({'sources': ['no_match.*']}, 'matches no inst.port'),
                                ({'sources': ['u_a.event_i']}, 'must be an output'),
                                ({'sources': ['u_a.intr_a_o', 'u_a.intr_a_o']}, 'duplicate IRQ source')]:
            with self.subTest(patch=patch):
                data = self.irq_data()
                data['irq'].update(patch)
                top, result = self.integrate_irq(data, '--irq-json', self.root/'irq.json', ok=False)
                self.assertIn(expected, result.stderr)
                self.assertFalse(top.exists())
                self.assertFalse((self.root/'irq.json').exists())

    def test_irq_glob_within_instance_uses_port_declaration_order(self):
        data = self.irq_data()
        data['irq']['sources'] = ['u_*.intr_*_o']
        data['irq']['reserve_zero'] = False
        table = self.root/'irq.json'
        self.integrate_irq(data, '--irq-json', table)
        self.assertEqual([e['source'] for e in json.loads(table.read_text())['irqs']],
                         ['u_b.intr_a_o', 'u_b.intr_b_o[1]', 'u_b.intr_b_o[2]',
                          'u_a.intr_a_o', 'u_a.intr_b_o[1]', 'u_a.intr_b_o[2]'])

    def test_irq_requires_section_for_exports_and_explicit_null_is_rejected(self):
        top, result = self.integrate_pad(None, '--irq-json', self.root/'irq.json', ok=False)
        self.assertIn('requires an irq section', result.stderr)
        self.assertFalse(top.exists())
        data = self.irq_data()
        data['mappings']['u_a.intr_a_o'] = None
        _, result = self.integrate_irq(data, ok=False)
        self.assertIn('u_a.intr_a_o must connect to a whole net', result.stderr)

    def domain_data(self):
        return {'instances': [{'module': 'domain_source', 'instance': 'u_src'},
                              {'module': 'domain_sink', 'instance': 'u_dst'}],
                'mappings': {'u_src.data_i': 'pad', 'u_dst.data_i': 'q', 'u_src.data_o': 'q'},
                'clocks': {'fast': {'net': 'clock_a', 'ports': ['u_src.tick']},
                           'slow': {'net': 'clock_b', 'ports': ['u_dst.sample']}},
                'resets': {'main': {'net': 'reset_n', 'ports': ['u_*.reset_n']}}}

    def integrate_domains(self, data=None, *args, ok=True):
        top = self.root/'top.sv'
        result = self.cli('integrate', FIXTURES/'domain_source.sv', FIXTURES/'domain_sink.sv',
                          '-o', top, '--map', self.mapping(self.domain_data() if data is None else data), *args, ok=ok)
        return top, result

    def test_declared_domains_drive_cdc_for_nonstandard_clock_names(self):
        top, result = self.integrate_domains()
        self.assertIn('u_src.data_o (fast) -> u_dst.data_i (slow)', result.stderr)
        self.assertIn('.tick(clock_a)', top.read_text())
        self.assertIn('.sample(clock_b)', top.read_text())
        self.lint(FIXTURES/'domain_source.sv', FIXTURES/'domain_sink.sv', top)
        result = self.cli('check', top, '--files', FIXTURES/'domain_source.sv', FIXTURES/'domain_sink.sv', '--strict', ok=False)
        self.assertIn('(fast)', result.stderr)
        data = self.domain_data()
        data['clocks'] = {'common': {'net': 'clock', 'ports': ['u_src.tick', 'u_dst.sample']}}
        self.integrate_domains(data, '--strict')  # Regeneration uses declared nets.

    def test_declared_domains_with_pin_annotation_and_irq_cdc(self):
        data = self.domain_data()
        data['clocks'] = {'main': {'net': 'clock', 'ports': ['u_src.tick', 'u_dst.sample']}}
        data['annotations'] = {'u_src.data_o': {'clock': 'tick'}}
        self.integrate_domains(data, '--strict')
        data = self.irq_data()
        data['clocks'] = {'source': {'net': 'clock_a', 'ports': ['u_a.clk_i', 'u_b.clk_i'], 'top': True},
                          'plic': {'net': 'clock_b', 'ports': ['u_plic.clk_i'], 'top': True}}
        _, result = self.integrate_irq(data)
        self.assertIn('u_a.intr_b_o (source) -> u_plic.intr_src_i (plic)', result.stderr)

    def test_net_name_pad_rename_survives_refresh(self):
        data = self.pad_data()
        data['pads'][-1]['from'] = 'u_uart_tx_o'
        top, _ = self.integrate_pad(data)
        before = top.read_bytes()
        self.cli('update', top, '--files', FIXTURES/'pad_unit.sv')
        self.assertEqual(before, top.read_bytes())

    def test_domain_manifest_patterns_chip_top_and_persisted_refresh(self):
        data = self.domain_data()
        del data['clocks'], data['resets']
        data.update(chip=True, pads=['pad', 'u_dst.data_o'])
        manifest = self.root/'domains.json'
        manifest.write_text(json.dumps([{'name': 'main', 'clk': 'clock', 'rst': 'reset_n', 'top': True,
                                         'ports': {'clk': ['u_src.tick', 'u_dst.sample'], 'rst': ['u_*.reset_n']}}]))
        top, result = self.integrate_domains(data, '--domains', manifest, '--strict')
        self.assertIn('Checks: 0 warning(s)', result.stderr)
        self.assertEqual(len(MODULE.select_module(top).ports), 4)
        before = top.read_bytes()
        manifest.unlink()  # Refresh uses persisted wiring, not an external file.
        self.cli('update', top, '--files', FIXTURES/'domain_source.sv', FIXTURES/'domain_sink.sv', '--strict')
        self.assertEqual(before, top.read_bytes())
        self.lint(FIXTURES/'domain_source.sv', FIXTURES/'domain_sink.sv', top)

    def test_domain_nets_not_implicit_chip_pads_and_explicit_map_wins(self):
        data = self.pad_data()
        data['pads'] = ['u_uart.pad_i', 'u_uart.tx_o']
        _, result = self.integrate_pad(data, ok=False)
        self.assertIn('u_uart.clk_i', result.stderr)
        self.assertIn('u_uart.rst_ni', result.stderr)
        data['mappings']['u_uart.clk_i'] = "1'b0"
        data['mappings']['u_uart.rst_ni'] = "1'b1"
        top, _ = self.integrate_pad(data)
        self.assertIn(".clk_i(1'b0)", top.read_text())
        self.lint(FIXTURES/'pad_unit.sv', top)

    def test_default_clock_reset_pattern_set(self):
        dut = self.source('dut', '''module dut(input clk, input clk_i, input clk_aux_i,
input rst_n, input rst_ni, input rst_aux_ni, output y);
assign y=clk ^ clk_i ^ clk_aux_i ^ rst_n ^ rst_ni ^ rst_aux_ni; endmodule''')
        data = {'chip': True, 'pads': ['clock', 'reset_n', 'u_dut.y'],
                'clocks': {'main': {'net': 'clock'}}, 'resets': {'main': {'net': 'reset_n'}}}
        top = self.root/'top.sv'
        self.cli('integrate', dut, '--map', self.mapping(data), '-o', top, '--strict')
        for port in ('clk', 'clk_i', 'clk_aux_i'):
            self.assertIn(f'.{port}(clock)', top.read_text())
        for port in ('rst_n', 'rst_ni', 'rst_aux_ni'):
            self.assertIn(f'.{port}(reset_n)', top.read_text())
        self.lint(dut, top)

    def test_domain_conflict_error_and_explicit_mapping_override(self):
        data = self.domain_data()
        data['clocks']['slow']['ports'].append('u_src.t*')
        top, result = self.integrate_domains(data, ok=False)
        self.assertIn('conflicting clock/reset domain matches for u_src.tick', result.stderr)
        self.assertFalse(top.exists())
        data['mappings']['u_src.tick'] = 'manual_clk'
        self.integrate_domains(data)  # Explicit mappings take precedence.

    def test_bad_domain_manifest_and_map_conflict_fail_before_write(self):
        manifest = self.root/'domains.json'
        for value, expected in [({}, 'JSON list'), ([{'name': 'main'}], 'clk'),
                                ([{'name': 'fast', 'clk': 'other', 'rst': 'reset'}], 'conflicting clocks')]:
            manifest.write_text(json.dumps(value))
            top, result = self.integrate_domains(None, '--domains', manifest, ok=False)
            self.assertIn(expected, result.stderr)
            self.assertFalse(top.exists())


if __name__ == '__main__':
    unittest.main()
