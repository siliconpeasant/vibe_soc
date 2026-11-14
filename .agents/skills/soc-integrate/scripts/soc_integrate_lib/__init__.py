"""Public compatibility API for the SoC integrator. CLI: soc_integrate_lib.cli."""
import argparse
import ast
import csv
import json
import operator
import re
import sys
import shutil
import shlex
import subprocess
import tempfile
import os
from bisect import bisect_right
from functools import lru_cache
import xml.etree.ElementTree as ET
from pathlib import Path
from .common import line_offsets, line_number, uncomment, fail, balanced, split_port_items, constant, constant_cached, resolve_param_width, resolved_width, bit_width, write_text, write_json, read_json_object
from .parse import VerilogModule, parse_parameters, parse_port, check_header_macros, parse_module
from .preprocess import Preprocessor, preprocess_sources, order_packages
from .extract import verilator_version, ast_constants, resolve_types, extract_sources, extract_modules, select_module
from .render import declaration, generate_instance, generate_port_declarations, generate_signal_declarations, generate_wrapper
from .portmap import PortMap
from .update import named_connections, user_regions, top_level_mask, preserved_instances, prune_preserved, metadata_paths, compact_metadata, read_metadata, parse_top, extract_map_from_top, port_changes, load_update, prune_map
from .checks import bus_like, selection_interval, net_base, literal_width, expression_width, port_signature, interface_shape, stale_map_checks, interface_array_checks, report_checks, compare_ports
from .build import default_instances, interface_signal, build_top, generate_top
from .lint import lint_collateral
from .cli import export_csv, emit_result, read_filelists, parser, main
from .common import IDENT, COMMENTS, NON_NEWLINE, INSTANCE_OPEN, INTERFACE_OPEN, INSTANCE_ARRAY, SEMICOLON
from .filelist import discover_sources, filelist_text, generate_filelist
from .ipxact import import_component, export_component
from .smoke import smoke_text, generate_smoke_tb
