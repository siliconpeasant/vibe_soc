"""Batch 3A: reusable filelists, executable smoke harnesses and component XML."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import test_integration as helpers
from test_parser import MODULE, SCRIPT

EXAMPLES = SCRIPT.parent.parent / 'examples'


class Batch3A(unittest.TestCase):
    setUp = helpers.IntegrationTest.setUp
    source = helpers.IntegrationTest.source
    mapping = helpers.IntegrationTest.mapping
    cli = helpers.IntegrationTest.cli
    lint = helpers.IntegrationTest.lint

    def test_flist_discovers_with_sibling_and_orders_packages(self):
        rtl = self.root / 'rtl with spaces'
        rtl.mkdir()
        base = rtl/'z_base_pkg.sv'
        base.write_text('package z_base_pkg; parameter W=8; endpackage\n')
        use = rtl/'a_use_pkg.sv'
        use.write_text('package a_use_pkg; typedef logic [z_base_pkg::W-1:0] word_t; endpackage\n')
        leaf = rtl/'leaf.sv'
        leaf.write_text('module leaf(input a_use_pkg::word_t x, output y); assign y=|x; endmodule\n')
        top = self.root/'top.sv'
        self.cli('integrate', leaf, '-o', top, '--package', use, '--package', base)
        manifest = self.root/'design.f'
        self.cli('flist', top, '--search-path', rtl, '-o', manifest, '-D', 'FEATURE=1', '-I', rtl, '-y', rtl)
        text = manifest.read_text()
        sources = [json.loads(line) for line in text.splitlines() if line.startswith('"/')]
        self.assertEqual(sources, [str(base), str(use), str(leaf), str(top)])
        self.assertIn('"-DFEATURE=1"', text)
        self.assertIn('"-I'+str(rtl)+'"', text)
        self.lint('-f', manifest)
        # Discovery is delegated, not a parallel scanner implementation.
        import soc_integrate_lib.filelist as flist
        original = __import__('importlib').util.spec_from_file_location
        calls = []
        def record(name, path):
            calls.append(str(path))
            return original(name, path)
        with patch.object(flist.importlib.util, 'spec_from_file_location', side_effect=record):
            self.assertIn(str(base), flist.discover_sources(rtl))
        self.assertTrue(any(p.endswith('soc-build/scripts/soc_gen_flist.py') for p in calls))

    def test_flist_recursion_options_and_native_interface_sources(self):
        nested = self.root/'nested'
        nested.mkdir()
        (nested/'extra.sv').write_text('module extra; endmodule\n')
        self.source('bus_if', "interface bus_if; wire a; assign a=1'b0; modport sink(input a); endinterface")
        leaf = self.source('leaf', 'module leaf(bus_if.sink bus, output y); assign y=bus.a; endmodule')
        top = self.root/'top.sv'
        self.cli('integrate', self.root/'bus_if.sv', leaf, '-o', top)
        self.cli('flist', top)
        text = top.with_suffix('.f').read_text()
        self.assertLess(text.index(str(self.root/'bus_if.sv')), text.index(str(leaf)))
        self.lint('-f', top.with_suffix('.f'))
        self.assertEqual(MODULE.discover_sources(nested, False), [str(nested/'extra.sv')])
        self.assertNotIn(str(nested/'extra.sv'), MODULE.discover_sources(self.root, False))

    def test_integrate_flist_and_smoke_run_real_verilator(self):
        source = EXAMPLES/'smoke/counter.sv'
        top = self.root/'top.sv'
        self.cli('integrate', source, '-o', top, '--flist', '--smoke-tb', '--cycles', 8)
        self.assertTrue(top.with_suffix('.f').exists())
        tb = self.root/'top_smoke_tb.sv'
        self.assertIn("tb_counter_rst_ni = 1'b0", tb.read_text())
        self.assertIn("tb_counter_rst_ni = 1'b1", tb.read_text())
        self.assertIn(".counter_enable_i('0)", tb.read_text())
        self.lint('-f', top.with_suffix('.f'))
        if not shutil.which('verilator'):
            self.skipTest('verilator unavailable')
        # Match the printed recipe, with --run using a disposable --Mdir.
        result = self.cli('smoke-tb', top, '--cycles', 8, '--run')
        self.assertIn('verilator --binary --timing -Wall', result.stdout)
        self.assertIn('PASS: top smoke (8 cycles)', result.stdout)
        self.assertIn('Verilog $finish', result.stdout)
        self.assertFalse((self.root/'obj_dir').exists())
        self.assertFalse((self.root/'top_smoke_tb_build').exists())

    def test_smoke_reset_polarities_and_no_clock(self):
        # The DUT asserts that both polarity conventions are exercised correctly.
        dut = self.source('dut', '''module dut(input clk_i, input rst_ni, input reset, output wire ok);
assign ok = rst_ni & ~reset;
always @(posedge clk_i) begin
    if ($time > 20 && !ok) $fatal(1, "reset did not release");
end
endmodule''')
        result = self.cli('smoke-tb', dut, '--cycles', 6, *(['--run'] if shutil.which('verilator') else []))
        text = (self.root/'dut_smoke_tb.sv').read_text()
        self.assertIn("logic tb_reset = 1'b1", text)
        self.assertIn("tb_reset = 1'b0", text)
        self.assertIn("logic tb_rst_ni = 1'b0", text)
        if shutil.which('verilator'):
            self.assertIn('PASS: dut smoke', result.stdout)
        comb = self.source('comb', 'module comb(input a, output y); assign y=a; endmodule')
        self.cli('smoke-tb', comb, '--cycles', 3, *(['--run'] if shutil.which('verilator') else []))

    def test_smoke_rejects_unsupported_and_invalid_options(self):
        for ports in ('inout wire pad', 'input [1:0] rst_n', 'bus_if.sink bus'):
            dut = self.source('dut', 'module dut('+ports+'); endmodule')
            self.cli('smoke-tb', dut, ok=False)
            self.assertFalse((self.root/'dut_smoke_tb.sv').exists())
        dut = self.source('dut', 'module dut(input a, output y); assign y=a; endmodule')
        for options in (('--cycles', 0), ('--cycles', 2), ('--reset-cycles', 0), ('--period', 3)):
            self.cli('smoke-tb', dut, *options, ok=False)

    def test_ipxact_roundtrip_ports_both_namespaces(self):
        source = self.source('dut', 'module dut(input wire a, input logic signed [1:0][7:0] x, output wire [0:3] y, inout wire z); endmodule')
        before = MODULE.select_module(source)
        for year in ('2014', '2022'):
            xml = self.root/f'dut-{year}.xml'
            self.cli('ipxact-export', source, '-o', xml, '--ipxact-version', year)
            after = MODULE.import_component(xml)
            self.assertEqual(after.ports, before.ports)
            self.assertEqual([d['type'] for d in after.details.values()], [d['type'] for d in before.details.values()])
            self.assertIn('1685-'+year, xml.read_text())
            self.assertEqual(json.loads(self.cli('extract', xml).stdout)['module_name'], 'dut')

    def test_ipxact_bus_groups_modes_and_integration_lint(self):
        example = EXAMPLES/'ipxact/gpio.xml'
        imported = MODULE.import_component(example)
        bus = imported.bus_interfaces[0]
        self.assertEqual(bus['name'], 'control')
        self.assertEqual(bus['bus_type']['name'], 'simple')
        self.assertEqual(bus['abstraction_types'][0]['port_maps'][0],
                         dict(logical_port='DATA', physical_port='data_i'))
        for year in ('2014', '2022'):
            for mode in ('master', 'slave', 'initiator', 'target'):
                imported.bus_interfaces[0]['mode'] = mode
                xml = self.root/'component.xml'
                MODULE.export_component(imported, xml, year)
                after = MODULE.import_component(xml).bus_interfaces
                expected_mode = ({'initiator': 'master', 'target': 'slave'} if year == '2014'
                                 else {'master': 'initiator', 'slave': 'target'}).get(mode, mode)
                self.assertEqual(after[0]['mode'], expected_mode)
                self.assertEqual(after[0]['abstraction_types'], imported.bus_interfaces[0]['abstraction_types'])
        top = self.root/'top.sv'
        self.cli('integrate', example, '-o', top)
        self.lint(EXAMPLES/'ipxact/gpio.sv', top)
        self.cli('update', top)
        self.lint(EXAMPLES/'ipxact/gpio.sv', top)
        self.assertIn('IP-XACT describes interfaces only', self.cli('flist', top, ok=False).stderr)
        self.cli('flist', top, '--files', EXAMPLES/'ipxact/gpio.sv')
        self.lint('-f', top.with_suffix('.f'))
        # Explicit known top bus grouping survives metadata then XML export.
        imported.bus_interfaces[0]['abstraction_types'][0]['port_maps'][0]['physical_port'] = 'gpio_data_i'
        mapping = self.mapping(dict(bus_interfaces=imported.bus_interfaces))
        self.cli('integrate', example, '-o', top, '--map', mapping)
        xml = self.root/'top.xml'
        self.cli('ipxact-export', top, '-o', xml)
        self.assertEqual(MODULE.import_component(xml).bus_interfaces[0]['mode'], 'slave')
        self.assertEqual(MODULE.import_component(xml).bus_interfaces[0]['abstraction_types'],
                         imported.bus_interfaces[0]['abstraction_types'])

    def test_ipxact_empty_module_parameters_and_prefix_independence(self):
        source = self.source('empty', 'module empty; endmodule')
        xml = self.root/'empty.xml'
        self.cli('ipxact-export', source, '-o', xml)
        self.assertEqual(MODULE.import_component(xml).ports, [])
        self.assertNotIn('<ipxact:ports', xml.read_text())
        source = self.source('dut', 'module dut #(parameter W=8)(input [W-1:0] x, output y); assign y=|x; endmodule')
        self.cli('ipxact-export', source, '-o', xml)
        xml.write_text(xml.read_text().replace('ipxact:', 'alt:').replace('xmlns:ipxact=', 'xmlns:alt='))
        imported = MODULE.import_component(xml)
        self.assertEqual(imported.params, [('W', '8', '')])
        self.assertEqual(imported.ports[0], ('input', '[W-1:0]', 'x'))
        top = self.root/'top.sv'
        self.cli('integrate', xml, '-o', top)
        self.lint(source, top)

    def test_ipxact_errors_and_export_boundaries(self):
        original = (EXAMPLES/'ipxact/gpio.xml').read_text()
        for content, message in (
            (original.replace('1685-2014', '1685-2009'), 'expected an IEEE'),
            (original.replace('<ipxact:direction>in<', '<ipxact:direction>phantom<'), 'unsupported direction'),
            (original.replace('<ipxact:name>data_i</ipxact:name></ipxact:physicalPort>', '<ipxact:name>absent</ipxact:name></ipxact:physicalPort>'), 'unknown physical port'),
            (original.replace('<ipxact:slave/>', ''), 'needs one supported'),
            (original.replace('<ipxact:slave/>', '<ipxact:mirroredSlave/>'), 'needs one supported'),
            (original.replace('</ipxact:physicalPort>', '<ipxact:partSelect/></ipxact:physicalPort>'), 'sliced port maps'),
        ):
            file = self.root/'bad.xml'
            file.write_text(content)
            self.assertIn(message, self.cli('ipxact-import', file, ok=False).stderr)
        for ports in ('input a [2]', 'bus_if.sink bus'):
            dut = self.source('dut', 'module dut('+ports+'); endmodule')
            out = self.root/'bad-export.xml'
            self.cli('ipxact-export', dut, '-o', out, ok=False)
            self.assertFalse(out.exists())
