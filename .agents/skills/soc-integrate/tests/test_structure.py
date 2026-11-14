"""Regression guard for the package split and historical import surface."""
import importlib
import ast
import unittest
from pathlib import Path
from test_parser import MODULE, SCRIPT


class StructureTest(unittest.TestCase):
    def test_legacy_public_symbols_and_module_ownership(self):
        names = ['line_offsets', 'line_number', 'uncomment', 'fail', 'balanced', 'split_port_items',
         'Preprocessor', 'constant', 'constant_cached', 'resolve_param_width', 'resolved_width',
         'bit_width', 'VerilogModule', 'parse_parameters', 'parse_port', 'check_header_macros',
         'parse_module', 'bus_like', 'selection_interval', 'verilator_version', 'ast_constants',
         'resolve_types', 'preprocess_sources', 'order_packages', 'extract_sources',
         'extract_modules', 'select_module', 'write_text', 'write_json', 'read_json_object',
         'declaration', 'generate_instance', 'generate_port_declarations',
         'generate_signal_declarations', 'generate_wrapper', 'PortMap', 'named_connections',
         'user_regions', 'top_level_mask', 'preserved_instances', 'prune_preserved',
         'metadata_paths', 'compact_metadata', 'read_metadata', 'parse_top', 'net_base',
         'literal_width', 'expression_width', 'default_instances', 'port_signature',
         'interface_shape', 'interface_signal', 'stale_map_checks', 'interface_array_checks',
         'build_top', 'generate_top', 'extract_map_from_top', 'port_changes', 'load_update',
         'report_checks', 'export_csv', 'lint_collateral', 'emit_result', 'compare_ports',
         'prune_map', 'read_filelists', 'parser', 'main']
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(MODULE, name)))
        self.assertLess(len(SCRIPT.read_text().splitlines()), 40)
        for name in ('parse', 'preprocess', 'portmap', 'build', 'update', 'checks', 'lint', 'cli'):
            self.assertTrue(importlib.import_module('soc_integrate_lib.' + name).__file__)
        self.assertEqual(MODULE.parse_port.__module__, 'soc_integrate_lib.parse')
        self.assertEqual(MODULE.build_top.__module__, 'soc_integrate_lib.build')

    def test_package_and_cli_generate_same_result(self):
        from soc_integrate_lib.parse import parse_module
        from soc_integrate_lib.build import generate_top
        source = 'module leaf(input a, output y); assign y = a; endmodule'
        self.assertEqual(MODULE.generate_top([MODULE.parse_module('leaf', source)]),
                         generate_top([parse_module('leaf', source)]))

    def test_regex_searches_use_precompiled_patterns(self):
        for source in (SCRIPT.parent/'soc_integrate_lib').glob('*.py'):
            for node in ast.walk(ast.parse(source.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == 're':
                        self.assertIn(node.func.attr, ('compile', 'escape', 'error'), str(source))
