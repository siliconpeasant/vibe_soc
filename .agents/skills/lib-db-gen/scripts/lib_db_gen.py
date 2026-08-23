#!/usr/bin/env python3
"""Generate Synopsys DB files from Liberty, or stub Liberty from Verilog ports."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Port:
    name: str
    direction: str
    msb: int | None = None
    lsb: int | None = None
    range_text: str = ""

    @property
    def is_bus(self) -> bool:
        return self.msb is not None and self.lsb is not None and self.msb != self.lsb

    @property
    def width(self) -> int:
        if self.msb is None or self.lsb is None:
            return 1
        return abs(self.msb - self.lsb) + 1


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*", "", text)
    return text


def split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    square = paren = brace = 0
    for index, char in enumerate(text):
        if char == "[":
            square += 1
        elif char == "]" and square:
            square -= 1
        elif char == "(":
            paren += 1
        elif char == ")" and paren:
            paren -= 1
        elif char == "{":
            brace += 1
        elif char == "}" and brace:
            brace -= 1
        elif char == "," and square == paren == brace == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unterminated module port list")


def find_module(text: str, top: str | None) -> tuple[str, str, str]:
    pattern = re.compile(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)")
    for match in pattern.finditer(text):
        name = match.group(1)
        if top and name != top:
            continue
        pos = match.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos < len(text) and text[pos] == "#":
            pos += 1
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos >= len(text) or text[pos] != "(":
                raise ValueError(f"malformed parameter list for module {name}")
            pos = matching_paren(text, pos) + 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != "(":
            continue
        end = matching_paren(text, pos)
        ports = text[pos + 1 : end]
        body_start = end + 1
        body_end_match = re.search(r"\bendmodule\b", text[body_start:])
        body_end = body_start + body_end_match.start() if body_end_match else len(text)
        return name, ports, text[body_start:body_end]
    wanted = top or "first module"
    raise ValueError(f"module not found: {wanted}")


def parse_range(tokens: list[str]) -> tuple[int | None, int | None, str, list[str]]:
    rest: list[str] = []
    msb = lsb = None
    range_text = ""
    for token in tokens:
        if token.startswith("[") and token.endswith("]"):
            range_text = token
            m = re.match(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", token)
            if m:
                msb, lsb = int(m.group(1)), int(m.group(2))
        else:
            rest.append(token)
    return msb, lsb, range_text, rest


def parse_decl_item(item: str, current_direction: str | None, current_range: tuple[int | None, int | None, str]) -> tuple[list[Port], str | None, tuple[int | None, int | None, str]]:
    item = item.strip().rstrip(")")
    item = re.sub(r"=.*$", "", item).strip()
    if not item:
        return [], current_direction, current_range
    tokens = item.replace(";", " ").split()
    direction = current_direction
    explicit_direction = False
    if tokens and tokens[0] in {"input", "output", "inout"}:
        direction = tokens.pop(0)
        explicit_direction = True
    if direction is None:
        return [], direction, current_range
    tokens = [tok for tok in tokens if tok not in {"wire", "reg", "logic", "tri", "signed", "unsigned", "var"}]
    msb, lsb, range_text, tokens = parse_range(tokens)
    if range_text:
        current_range = (msb, lsb, range_text)
    elif explicit_direction:
        current_range = (None, None, "")
    elif tokens and current_direction == direction:
        msb, lsb, range_text = current_range
    names: list[str] = []
    for token in tokens:
        clean = token.strip().strip(",")
        m = re.match(r"([A-Za-z_][A-Za-z0-9_$]*)", clean)
        if m:
            names.append(m.group(1))
    return [Port(name, direction, msb, lsb, range_text) for name in names], direction, current_range


def parse_verilog_ports(top_v: Path, top: str | None) -> tuple[str, list[Port], list[str]]:
    text = strip_comments(top_v.read_text(errors="replace"))
    module, port_text, body = find_module(text, top)
    warnings: list[str] = []
    ports: list[Port] = []
    current_direction: str | None = None
    current_range: tuple[int | None, int | None, str] = (None, None, "")
    ansi_seen = False
    for item in split_top_level_commas(port_text):
        if re.search(r"\b(input|output|inout)\b", item):
            ansi_seen = True
        parsed, current_direction, current_range = parse_decl_item(item, current_direction, current_range)
        ports.extend(parsed)
    if not ansi_seen or not ports:
        port_order = [p.strip().strip(".") for p in split_top_level_commas(port_text)]
        decls: dict[str, Port] = {}
        for match in re.finditer(r"\b(input|output|inout)\b\s+([^;]+);", body, flags=re.S):
            direction = match.group(1)
            decl_body = match.group(2).replace("\n", " ")
            msb = lsb = None
            range_text = ""
            range_match = re.search(r"\[[^\]]+\]", decl_body)
            if range_match:
                range_text = range_match.group(0)
                nums = re.match(r"\[\s*(-?\d+)\s*:\s*(-?\d+)\s*\]", range_text)
                if nums:
                    msb, lsb = int(nums.group(1)), int(nums.group(2))
            decl_body = re.sub(r"\[[^\]]+\]", " ", decl_body)
            decl_body = re.sub(r"\b(wire|reg|logic|tri|signed|unsigned|var)\b", " ", decl_body)
            for name in split_top_level_commas(decl_body):
                m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_$]*)", name)
                if m:
                    decls[m.group(1)] = Port(m.group(1), direction, msb, lsb, range_text)
        ports = [decls[name] for name in port_order if name in decls]
    seen: set[str] = set()
    unique_ports: list[Port] = []
    for port in ports:
        if port.name in seen:
            continue
        seen.add(port.name)
        if port.range_text and not port.is_bus and not re.match(r"\[\s*-?\d+\s*:\s*-?\d+\s*\]", port.range_text):
            warnings.append(f"parameterized or non-numeric range on {port.name} treated as scalar: {port.range_text}")
        unique_ports.append(port)
    if not unique_ports:
        raise ValueError(f"no ports parsed for module {module}")
    return module, unique_ports, warnings


def liberty_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def bus_type_name(port: Port) -> str:
    return f"bus_{port.width}_{port.msb}_{port.lsb}".replace("-", "m")


def generate_stub_lib(library: str, cell: str, ports: list[Port]) -> str:
    bus_ports = [port for port in ports if port.is_bus]
    lines = [
        f"library ({liberty_name(library)}) {{",
        '  delay_model : table_lookup;',
        '  time_unit : "1ns";',
        '  voltage_unit : "1V";',
        '  current_unit : "1mA";',
        '  pulling_resistance_unit : "1kohm";',
        '  leakage_power_unit : "1nW";',
        '  capacitive_load_unit (1, pf);',
        '  nom_process : 1.0;',
        '  nom_temperature : 25.0;',
        '  nom_voltage : 1.0;',
        '',
    ]
    emitted_types: set[str] = set()
    for port in bus_ports:
        name = bus_type_name(port)
        if name in emitted_types:
            continue
        emitted_types.add(name)
        downto = "true" if port.msb is not None and port.lsb is not None and port.msb > port.lsb else "false"
        lines.extend([
            f"  type ({name}) {{",
            '    base_type : array;',
            '    data_type : bit;',
            f"    bit_width : {port.width};",
            f"    bit_from : {port.msb};",
            f"    bit_to : {port.lsb};",
            f"    downto : {downto};",
            '  }',
            '',
        ])
    lines.extend([
        f"  cell ({liberty_name(cell)}) {{",
        '    area : 0.0;',
        '    dont_use : true;',
        '    dont_touch : true;',
        '    is_macro_cell : true;',
    ])
    for port in ports:
        direction = "input" if port.direction == "input" else "output" if port.direction == "output" else "inout"
        if port.is_bus:
            lines.extend([
                f"    bus ({liberty_name(port.name)}) {{",
                f"      bus_type : {bus_type_name(port)};",
                f"      direction : {direction};",
            ])
            if direction == "input":
                lines.append('      capacitance : 0.0;')
            lines.append('    }')
        else:
            lines.extend([
                f"    pin ({liberty_name(port.name)}) {{",
                f"      direction : {direction};",
            ])
            if direction == "input":
                lines.append('      capacitance : 0.0;')
            elif direction == "output":
                lines.append('      function : "0";')
            lines.append('    }')
    lines.extend(['  }', '}'])
    return "\n".join(lines) + "\n"


def parse_lib_name(lib_path: Path) -> str:
    text = strip_comments(lib_path.read_text(errors="replace"))
    match = re.search(r"\blibrary\s*\(\s*([^\s\)]+)\s*\)", text)
    if not match:
        raise ValueError(f"could not find library (...) name in {lib_path}")
    return match.group(1).strip('"')


SUPPORTED_DB_SHELL_MODES = ("auto", "dc", "lc")


def write_db_tcl(
    lib_path: Path,
    db_path: Path,
    tcl_path: Path,
    lib_name: str,
    *,
    backend: str,
) -> None:
    """Emit the tool-specific convert Tcl.

    backend:
      - ``lc``: native Library Compiler session
      - ``dc``: Design Compiler write-lib mode (enable_write_lib_mode)

    On some RHEL 8 hosts LC X-2025.06 successfully write_lib then SIGSEGVs in
    process exit handlers after any read_lib. DC write-lib mode has been
    observed to write the same DB and exit 0 cleanly.
    """
    if backend not in {"lc", "dc"}:
        raise ValueError(f"unsupported DB backend: {backend}")
    lib_abs = lib_path.resolve().as_posix()
    db_abs = db_path.resolve().as_posix()
    tcl_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if backend == "dc":
        # Required before write_lib in dc_shell (UIL-91 when omitted).
        lines.append("enable_write_lib_mode")
    lines.extend(
        [
            f'read_lib "{lib_abs}"',
            f'write_lib {lib_name} -format db -output "{db_abs}"',
            "exit",
            "",
        ]
    )
    tcl_path.write_text("\n".join(lines), encoding="utf-8")


def write_lc_tcl(lib_path: Path, db_path: Path, tcl_path: Path, lib_name: str) -> None:
    """Backward-compatible alias: emit LC-style convert Tcl."""
    write_db_tcl(lib_path, db_path, tcl_path, lib_name, backend="lc")


def default_work_dir(db_path: Path) -> Path:
    return db_path.parent / "lc_work"


def default_tcl_path(db_path: Path, work_dir: Path) -> Path:
    return work_dir / f"{db_path.stem}.lc.tcl"


def reject_path_collisions(paths: dict[str, Path]) -> None:
    resolved_paths: dict[Path, str] = {}
    for label, path in paths.items():
        resolved = path.expanduser().resolve()
        previous = resolved_paths.get(resolved)
        if previous is not None:
            raise ValueError(
                f"path collision: {label} and {previous} resolve to {resolved}"
            )
        resolved_paths[resolved] = label


def staging_db_path(db_path: Path) -> Path:
    return db_path.with_name(f".{db_path.name}.{uuid.uuid4().hex}.tmp.db")


def _resolve_executable(name_or_path: str) -> str | None:
    if not name_or_path:
        return None
    path = Path(name_or_path)
    if path.is_file() and os.access(path, os.X_OK):
        return str(path)
    found = shutil.which(name_or_path)
    return found


def resolve_db_backend(
    mode: str,
    *,
    lc_shell: str,
    dc_shell: str,
) -> tuple[str, str]:
    """Return (backend, executable path) for Liberty→DB conversion."""
    # Default backend is DC write-lib mode (avoids LC exit-handler SIGSEGV).
    mode = (mode or "dc").strip().lower()
    if mode not in SUPPORTED_DB_SHELL_MODES:
        raise ValueError(
            f"shell mode must be one of: {', '.join(SUPPORTED_DB_SHELL_MODES)}"
        )

    lc_exe = _resolve_executable(lc_shell)
    dc_exe = _resolve_executable(dc_shell)

    if mode == "dc":
        if not dc_exe:
            raise FileNotFoundError(
                f"dc_shell not found ({dc_shell}); set DC_SHELL or --dc-shell"
            )
        return "dc", dc_exe
    if mode == "lc":
        if not lc_exe:
            raise FileNotFoundError(
                f"lc_shell not found ({lc_shell}); set LC_SHELL or --lc-shell"
            )
        return "lc", lc_exe

    # auto: prefer DC; fall back to LC only when DC is unavailable.
    if dc_exe:
        return "dc", dc_exe
    if lc_exe:
        return "lc", lc_exe
    raise FileNotFoundError(
        "neither dc_shell nor lc_shell found; set DC_SHELL/LC_SHELL or --dc-shell/--lc-shell"
    )


def _staged_db_ready(staged_db_path: Path) -> bool:
    return staged_db_path.is_file() and staged_db_path.stat().st_size > 0


def _is_crash_exit(returncode: int | None) -> bool:
    """True only for the observed LC post-write SIGSEGV encodings.

    subprocess reports signal death as a negative code (-N). Some wrappers
    report 128+N instead. Do not recover SIGKILL, SIGTERM, SIGABRT, or other
    fatal signals: they may leave a partial .db that merely happens to be
    non-empty.
    """
    if returncode is None:
        return False
    # subprocess: -SIGSEGV; wrappers: bare 11 or 128 + SIGSEGV = 139.
    return returncode in {-11, 11, 139}


def _recover_lc_post_write_crash(
    returncode: int,
    staged_db_path: Path,
) -> bool:
    """Return True if LC wrote a usable DB then crashed in exit handlers."""
    if not _is_crash_exit(returncode):
        return False
    if not _staged_db_ready(staged_db_path):
        return False
    print(
        "[LIBDB] WARNING: lc_shell exited with status "
        f"{returncode} after writing a non-empty DB "
        f"({staged_db_path}). Treating conversion as success "
        "(known LC X-2025.06 exit-handler SIGSEGV after read_lib). "
        "Prefer --shell-mode dc (dc_shell + enable_write_lib_mode) for a "
        "clean process exit, or upgrade/patch Library Compiler.",
        file=sys.stderr,
    )
    return True


def run_db_shell(
    exe: str,
    tcl_path: Path,
    work_dir: Path,
    staged_db_path: Path,
    *,
    backend: str,
) -> None:
    """Run DC/LC convert Tcl and enforce DB production.

    LC on some hosts (observed: RHEL 8.10 + LC X-2025.06) may write a valid
    .db then SIGSEGV during exit handlers after read_lib. When backend is ``lc``
    and the staged DB is non-empty after a crash exit, treat that as success
    with a warning so callers still install the artifact. DC write-lib mode is
    preferred because it has been observed to exit 0 cleanly.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [exe, "-f", str(tcl_path.resolve())],
        cwd=work_dir,
        check=False,
    )
    if result.returncode == 0:
        return
    if backend == "lc" and _recover_lc_post_write_crash(
        result.returncode, staged_db_path
    ):
        return
    raise RuntimeError(
        f"{backend}_shell failed with status {result.returncode}: {exe} -f {tcl_path}"
    )


def run_lc_shell(lc_shell: str, tcl_path: Path, work_dir: Path) -> None:
    """Run Library Compiler; unit tests may monkeypatch this hook.

    Production callers should prefer :func:`run_db_shell` (via finalize) so
    post-write SIGSEGV recovery is applied. This thin wrapper keeps the
    historical test seam and still surfaces crash exits as CalledProcessError.
    """
    exe = _resolve_executable(lc_shell) or lc_shell
    work_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, "-f", str(tcl_path.resolve())], cwd=work_dir, check=True)


def run_lc_shell_and_finalize_tcl(
    lc_shell: str,
    tcl_path: Path,
    work_dir: Path,
    staged_db_path: Path,
    db_path: Path,
    lib_path: Path,
    lib_name: str,
    *,
    keep_tcl: bool,
    backend: str = "lc",
    shell_exe: str | None = None,
) -> None:
    # Cleanup intentionally happens only after a usable DB is produced. A failed
    # conversion leaves the exact command file available for diagnosis.
    exe = shell_exe or lc_shell
    if backend == "dc":
        # Clean-exit path: dc_shell + enable_write_lib_mode.
        run_db_shell(exe, tcl_path, work_dir, staged_db_path, backend="dc")
    else:
        # LC path keeps the run_lc_shell hook (unit tests monkeypatch it).
        # Stock implementation raises CalledProcessError on SIGSEGV; recover
        # when a non-empty staged DB was produced (known LC exit-handler crash).
        try:
            run_lc_shell(exe, tcl_path, work_dir)
        except subprocess.CalledProcessError as exc:
            if not _recover_lc_post_write_crash(exc.returncode, staged_db_path):
                raise RuntimeError(
                    f"lc_shell failed with status {exc.returncode}: "
                    f"{exe} -f {tcl_path}"
                ) from exc
    if not _staged_db_ready(staged_db_path):
        raise RuntimeError(
            f"{backend}_shell completed without a non-empty current-run DB output: "
            f"{staged_db_path}"
        )
    staged_db_path.replace(db_path)
    if keep_tcl:
        # Preserve a reusable command file that targets the final DB path.
        # On failure, the untouched Tcl continues to reference the staged path.
        write_db_tcl(lib_path, db_path, tcl_path, lib_name, backend=backend)
        print(f"[LIBDB] Tcl retained: {tcl_path}")
        return
    tcl_path.unlink(missing_ok=True)
    print(f"[LIBDB] Tcl removed after successful conversion: {tcl_path}")


def cmd_convert(args: argparse.Namespace) -> int:
    lib_path = Path(args.lib)
    db_path = Path(args.db)
    work_dir = Path(args.work_dir) if args.work_dir else default_work_dir(db_path)
    tcl_path = Path(args.tcl) if args.tcl else default_tcl_path(db_path, work_dir)
    reject_path_collisions(
        {
            "--lib": lib_path,
            "--db": db_path,
            "--tcl": tcl_path,
        }
    )
    if not lib_path.is_file():
        raise FileNotFoundError(lib_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    lib_name = args.library_name or parse_lib_name(lib_path)
    run_db_path = db_path if args.no_run else staging_db_path(db_path)

    shell_mode = getattr(args, "shell_mode", None) or os.environ.get(
        "LIB_DB_SHELL_MODE", "dc"
    )
    dc_shell = getattr(args, "dc_shell", None) or os.environ.get("DC_SHELL", "dc_shell")
    if args.no_run:
        # Default offline Tcl matches production backend (dc write-lib mode).
        no_run_backend = "lc" if str(shell_mode).strip().lower() == "lc" else "dc"
        write_db_tcl(lib_path, run_db_path, tcl_path, lib_name, backend=no_run_backend)
        print(f"[LIBDB] Tcl:  {tcl_path}")
        print(f"[LIBDB] Work: {work_dir}")
        print("[LIBDB] --no-run set; not invoking dc_shell/lc_shell")
        return 0

    backend, shell_exe = resolve_db_backend(
        shell_mode, lc_shell=args.lc_shell, dc_shell=dc_shell
    )
    write_db_tcl(lib_path, run_db_path, tcl_path, lib_name, backend=backend)
    print(f"[LIBDB] Backend: {backend} ({shell_exe})")
    print(f"[LIBDB] Tcl:  {tcl_path}")
    print(f"[LIBDB] Work: {work_dir}")
    run_lc_shell_and_finalize_tcl(
        args.lc_shell,
        tcl_path,
        work_dir,
        run_db_path,
        db_path,
        lib_path,
        lib_name,
        keep_tcl=args.keep_tcl,
        backend=backend,
        shell_exe=shell_exe,
    )
    print(f"[LIBDB] DB:   {db_path}")
    return 0


def cmd_stub(args: argparse.Namespace) -> int:
    top_v = Path(args.top_v)
    lib_path = Path(args.lib)
    db_path = Path(args.db)
    work_dir = Path(args.work_dir) if args.work_dir else default_work_dir(db_path)
    tcl_path = Path(args.tcl) if args.tcl else default_tcl_path(db_path, work_dir)
    reject_path_collisions(
        {
            "--top-v": top_v,
            "--lib": lib_path,
            "--db": db_path,
            "--tcl": tcl_path,
        }
    )
    if not top_v.is_file():
        raise FileNotFoundError(top_v)
    module, ports, warnings = parse_verilog_ports(top_v, args.top)
    lib_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    library_name = args.library_name or f"{module}_stub_lib"
    lib_path.write_text(generate_stub_lib(library_name, module, ports), encoding="utf-8")
    lib_name = liberty_name(library_name)
    run_db_path = db_path if args.no_run else staging_db_path(db_path)
    print(f"[LIBDB] Parsed module: {module}")
    print(f"[LIBDB] Ports: {len(ports)}")
    for warning in warnings:
        print(f"[LIBDB] WARNING: {warning}", file=sys.stderr)
    print(f"[LIBDB] Liberty: {lib_path}")
    shell_mode = getattr(args, "shell_mode", None) or os.environ.get(
        "LIB_DB_SHELL_MODE", "dc"
    )
    dc_shell = getattr(args, "dc_shell", None) or os.environ.get("DC_SHELL", "dc_shell")
    if args.no_run:
        no_run_backend = "lc" if str(shell_mode).strip().lower() == "lc" else "dc"
        write_db_tcl(lib_path, run_db_path, tcl_path, lib_name, backend=no_run_backend)
        print(f"[LIBDB] Tcl:     {tcl_path}")
        print(f"[LIBDB] Work:    {work_dir}")
        print("[LIBDB] --no-run set; not invoking dc_shell/lc_shell")
        return 0

    backend, shell_exe = resolve_db_backend(
        shell_mode, lc_shell=args.lc_shell, dc_shell=dc_shell
    )
    write_db_tcl(lib_path, run_db_path, tcl_path, lib_name, backend=backend)
    print(f"[LIBDB] Backend: {backend} ({shell_exe})")
    print(f"[LIBDB] Tcl:     {tcl_path}")
    print(f"[LIBDB] Work:    {work_dir}")
    run_lc_shell_and_finalize_tcl(
        args.lc_shell,
        tcl_path,
        work_dir,
        run_db_path,
        db_path,
        lib_path,
        lib_name,
        keep_tcl=args.keep_tcl,
        backend=backend,
        shell_exe=shell_exe,
    )
    print(f"[LIBDB] DB:      {db_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lc-shell", default=os.environ.get("LC_SHELL", "lc_shell"))
    parser.add_argument(
        "--dc-shell",
        default=os.environ.get("DC_SHELL", "dc_shell"),
        help="Design Compiler shell (default backend; write-lib mode)",
    )
    parser.add_argument(
        "--shell-mode",
        default=os.environ.get("LIB_DB_SHELL_MODE", "dc"),
        choices=sorted(SUPPORTED_DB_SHELL_MODES),
        help="dc (default): dc_shell + enable_write_lib_mode; "
        "auto: prefer dc, fall back to lc; lc: Library Compiler (may SIGSEGV on exit)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="Convert an existing Liberty .lib to Synopsys .db")
    convert.add_argument("--lc-shell", default=argparse.SUPPRESS)
    convert.add_argument("--dc-shell", default=argparse.SUPPRESS)
    convert.add_argument("--shell-mode", default=argparse.SUPPRESS, choices=sorted(SUPPORTED_DB_SHELL_MODES))
    convert.add_argument("--lib", required=True)
    convert.add_argument("--db", required=True)
    convert.add_argument("--tcl", help="override the temporary Library Compiler Tcl path")
    convert.add_argument("--work-dir")
    convert.add_argument("--library-name")
    convert.add_argument("--no-run", action="store_true")
    convert.add_argument(
        "--keep-tcl",
        action="store_true",
        help="retain the Library Compiler Tcl after a successful conversion",
    )
    convert.set_defaults(func=cmd_convert)

    stub = sub.add_parser("stub", help="Generate stub Liberty from a Verilog top module and optionally compile to .db")
    stub.add_argument("--lc-shell", default=argparse.SUPPRESS)
    stub.add_argument("--dc-shell", default=argparse.SUPPRESS)
    stub.add_argument("--shell-mode", default=argparse.SUPPRESS, choices=sorted(SUPPORTED_DB_SHELL_MODES))
    stub.add_argument("--top-v", required=True)
    stub.add_argument("--top")
    stub.add_argument("--lib", required=True)
    stub.add_argument("--db", required=True)
    stub.add_argument("--tcl", help="override the temporary Library Compiler Tcl path")
    stub.add_argument("--work-dir")
    stub.add_argument("--library-name")
    stub.add_argument("--no-run", action="store_true")
    stub.add_argument(
        "--keep-tcl",
        action="store_true",
        help="retain the Library Compiler Tcl after a successful conversion",
    )
    stub.set_defaults(func=cmd_stub)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[LIBDB] ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
