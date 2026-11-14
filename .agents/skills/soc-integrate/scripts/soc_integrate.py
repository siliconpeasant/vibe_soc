#!/usr/bin/env python3
"""Backward-compatible entry point for the stdlib SoC interface/integration tools."""
import sys
from pathlib import Path

# Also support importlib.spec_from_file_location callers outside scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from soc_integrate_lib import *  # noqa: F403 -- historical public import surface
from soc_integrate_lib import extract as _extract


def resolve_types(module, packages, include_dirs, defines):
    """Keep the legacy version-detection injection seam for library callers."""
    return _extract.resolve_types(module, packages, include_dirs, defines,
                                  version_detector=verilator_version)


if __name__ == '__main__':
    sys.exit(main())
