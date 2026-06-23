#!/usr/bin/env python3
"""Run module simulations over a test/seed matrix and emit machine-readable results."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shlex
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestSpec:
    name: str
    args: str = ""


@dataclass
class Result:
    test: str
    seed: int
    status: str
    returncode: int
    log: str
    command: str


def load_tests(path: Path | None, inline: str) -> list[TestSpec]:
    specs: list[TestSpec] = []
    if path and path.is_file():
        lines = path.read_text(errors="replace").splitlines()
    else:
        lines = [item.strip() for item in inline.split(",") if item.strip()] or ["default"]
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(maxsplit=1)
        specs.append(TestSpec(parts[0], parts[1] if len(parts) > 1 else ""))
    return specs


def load_seeds(value: str) -> list[int]:
    seeds: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            start, end = (int(part) for part in item.split("-", 1))
            seeds.extend(range(start, end + 1))
        else:
            seeds.append(int(item))
    return seeds or [1]


def run_one(
    sim_dir: Path,
    output_dir: Path,
    base_command: str,
    spec: TestSpec,
    seed: int,
    pass_regex: str,
    fail_regex: str,
    matrix_args: str,
) -> Result:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", spec.name)
    log_path = output_dir / f"{safe_name}_seed_{seed}.log"
    test_args = f"+TESTNAME={shlex.quote(spec.name)} +UVM_TESTNAME={shlex.quote(spec.name)}"
    per_run_args = matrix_args.format(test=safe_name, seed=seed)
    command = f"{base_command} {test_args} +ntb_random_seed={seed} {spec.args} {per_run_args}".strip()
    env = os.environ.copy()
    env.update({"TEST": spec.name, "SEED": str(seed)})
    with log_path.open("w") as log:
        completed = subprocess.run(
            command,
            cwd=sim_dir,
            env=env,
            shell=True,
            executable="/bin/bash",
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    text = log_path.read_text(errors="replace")
    passed = completed.returncode == 0
    if pass_regex:
        passed = passed and re.search(pass_regex, text, re.MULTILINE) is not None
    if fail_regex and re.search(fail_regex, text, re.MULTILINE | re.IGNORECASE):
        passed = False
    return Result(
        test=spec.name,
        seed=seed,
        status="PASS" if passed else "FAIL",
        returncode=completed.returncode,
        log=str(log_path),
        command=command,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--tests-file", type=Path)
    parser.add_argument("--tests", default="default")
    parser.add_argument("--seeds", default="1")
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--pass-regex", default="")
    parser.add_argument("--matrix-args", default="")
    parser.add_argument(
        "--fail-regex",
        default=r"\[(?:ERROR|FAIL)\]|MISMATCH|ERROR=[1-9][0-9]*|^RESULT:(?!\s*ALL TESTS PASS)",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    tests = load_tests(args.tests_file, args.tests)
    matrix = [(test, seed) for test in tests for seed in load_seeds(args.seeds)]
    results: list[Result] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        futures = [
            executor.submit(
                run_one,
                args.sim_dir,
                args.output_dir,
                args.command,
                test,
                seed,
                args.pass_regex,
                args.fail_regex,
                args.matrix_args,
            )
            for test, seed in matrix
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda item: (item.test, item.seed))
    passed = sum(result.status == "PASS" for result in results)
    failed = len(results) - passed
    summary = {"total": len(results), "passed": passed, "failed": failed, "results": [asdict(r) for r in results]}
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [f"{result.status:4} test={result.test} seed={result.seed} log={result.log}" for result in results]
    lines.append(f"TOTAL={len(results)} PASS={passed} FAIL={failed}")
    (args.output_dir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
