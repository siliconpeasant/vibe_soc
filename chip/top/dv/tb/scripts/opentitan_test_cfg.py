#!/usr/bin/env python3
"""Render vibe_soc OpenTitan test index fields for Makefile consumption."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


FIELDS = {
    "uvm_test",
    "uvm_sequence",
    "run_opts",
    "compile_opts",
    "sw_images",
    "timeout_ns",
    "waves",
    "status",
}


def load_yaml_cfg(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        meaningful = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        if meaningful in ([], ["overrides: {}"]):
            data = {"overrides": {}}
        else:
            raise SystemExit(f"PyYAML is required for non-empty YAML overrides: {path}")
    if not isinstance(data, dict):
        raise SystemExit(f"invalid test YAML: {path}")
    return data


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"invalid test JSON: {path}")
    return data


def merge_dict(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def load_index_cfg(manifest_path: Path, test_name: str) -> dict:
    manifest = load_json(manifest_path)
    root = manifest_path.parent
    found = None
    for case_file in manifest.get("case_files") or []:
        shard_path = root / case_file
        shard = load_json(shard_path)
        cases = shard.get("cases") or {}
        if test_name in cases:
            found = cases[test_name]
            break
    if found is None:
        raise SystemExit(f"missing OpenTitan test in index: {test_name}")
    if not isinstance(found, dict):
        raise SystemExit(f"invalid OpenTitan test entry: {test_name}")

    overrides_file = manifest.get("overrides")
    if overrides_file:
        overrides_path = root / overrides_file
        if overrides_path.exists():
            overrides = load_yaml_cfg(overrides_path).get("overrides") or {}
            test_override = overrides.get(test_name) or {}
            if test_override:
                if not isinstance(test_override, dict):
                    raise SystemExit(f"invalid OpenTitan override entry: {test_name}")
                found = merge_dict(found, test_override)
    return found


def shell_words(items) -> str:
    if not items:
        return ""
    return " ".join(str(item) for item in items if str(item))


def module_root(config_file: Path) -> Path:
    # chip/top/dv/tb/tests/<config> -> chip/top
    return config_file.resolve().parents[3]


def resolve_base(config_file: Path, base: str) -> str:
    path = Path(base)
    if path.is_absolute():
        return path.as_posix()
    if base.startswith("dv/") or base.startswith("de/") or base.startswith("docs/"):
        return (module_root(config_file) / path).as_posix()
    return base


def sw_images(cfg: dict, config_file: Path) -> str:
    sw = cfg.get("sw_collateral") or {}
    images = []
    for image in sw.get("images") or []:
        base = image.get("base")
        slot = image.get("slot")
        rule = image.get("rule")
        if not base or slot is None:
            continue
        entry = f"{resolve_base(config_file, str(base))}:{slot}"
        if rule:
            entry = f"{entry}:{rule}"
        images.append(entry)
    test_rom = sw.get("test_rom") or {}
    if test_rom.get("base") and test_rom.get("slot") is not None:
        images.append(f"{resolve_base(config_file, str(test_rom['base']))}:{test_rom['slot']}")
    return ",".join(images)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_file", type=Path)
    parser.add_argument("query", nargs="+")
    args = parser.parse_args()

    if args.config_file.suffix in {".yml", ".yaml"} and len(args.query) == 1:
        # Backward compatible path for local debugging with a legacy case YAML.
        field = args.query[0]
        cfg = load_yaml_cfg(args.config_file)
    elif len(args.query) == 2:
        test_name, field = args.query
        cfg = load_index_cfg(args.config_file, test_name)
    else:
        raise SystemExit("usage: opentitan_test_cfg.py <manifest.json> <test> <field>")

    if field not in FIELDS:
        raise SystemExit(f"unknown OpenTitan test field: {field}")

    if field == "run_opts":
        print(shell_words(cfg.get("run_opts") or []))
    elif field == "compile_opts":
        print(shell_words(cfg.get("compile_opts") or []))
    elif field == "sw_images":
        print(sw_images(cfg, args.config_file))
    else:
        value = cfg.get(field, "")
        print("" if value is None else value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
