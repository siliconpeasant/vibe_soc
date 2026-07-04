#!/usr/bin/env python3
"""Parse lint reports and track autofix benchmark rounds.

This script supports SpyGlass moresimple reports. It does not edit RTL.
It records the observable lint state after each No-KB or With-KB
repair attempt so both approaches can be compared by elapsed repair time and
number of rounds to convergence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def summarize(path: Path, tags: dict[str, dict[str, Any]], report_format: str) -> dict[str, Any]:
    total_findings = sum(int(v.get("count", 0)) for v in tags.values())
    info_messages = sum(int(v.get("severities", {}).get("info", 0)) for v in tags.values())
    total_violations = 0
    for rec in tags.values():
        severities = rec.get("severities", {})
        total_violations += sum(
            int(count) for sev, count in severities.items() if sev.lower() != "info"
        )
    return {
        "report": str(path),
        "format": report_format,
        "unique_tags": len(tags),
        "total_violations": total_violations,
        "total_findings": total_findings,
        "info_messages": info_messages,
        "tags": sorted(tags.values(), key=lambda x: (-int(x.get("count", 0)), x["tag"])),
    }


def parse_spyglass_report(path: Path, text: str) -> dict[str, Any]:
    tags: dict[str, dict[str, Any]] = {}

    for line in text.splitlines():
        if not SPYGLASS_ROW_RE.match(line):
            continue
        parts = re.split(r"\s{2,}", line.strip())
        if len(parts) < 6:
            continue
        rule = parts[1]
        sev_idx = -1
        sev = ""
        for idx in range(2, len(parts)):
            normalized = SPYGLASS_SEVERITIES.get(parts[idx].strip().lower())
            if normalized:
                sev_idx = idx
                sev = normalized
                break
        if sev_idx < 0 or sev_idx + 3 >= len(parts):
            continue
        filename = parts[sev_idx + 1]
        line_no = parts[sev_idx + 2]
        message = parts[sev_idx + 4] if sev_idx + 4 < len(parts) else ""
        rec = tags.setdefault(rule, {"tag": rule, "count": 0, "severities": {}, "examples": []})
        rec["count"] += 1
        rec["severities"][sev] = rec["severities"].get(sev, 0) + 1
        rec["examples"].append({
            "tag": rule,
            "filename": filename,
            "linenumber": line_no,
            "description": message,
        })

    return summarize(path, tags, "spyglass")


def parse_report(path: Path) -> dict[str, Any]:
    text = path.read_text(errors="replace")
    if "MORESIMPLE REPORT" in text and "SpyGlass" in text:
        return parse_spyglass_report(path, text)
    raise ValueError(f"Unsupported lint report format for {path}; expected SpyGlass moresimple report")


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        return json.loads(path.read_text())
    return default


def render_round_table(rounds: list[dict[str, Any]]) -> str:
    lines = [
        "| Mode | Round | Elapsed s | Unique tags | Violations | Infos | New tags | Cleared tags | Report |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    prev_by_mode: dict[str, set[str]] = {}
    for r in rounds:
        tags = set(r.get("tag_names", []))
        prev = prev_by_mode.get(r["mode"], set())
        new = len(tags - prev) if prev else len(tags)
        cleared = len(prev - tags) if prev else 0
        prev_by_mode[r["mode"]] = tags
        lines.append(
            f"| {r['mode']} | {r['round']} | {r.get('elapsed_seconds', 0):.1f} | "
            f"{r['unique_tags']} | {r['total_violations']} | {r.get('info_messages', 0)} | "
            f"{new} | {cleared} | `{r['report']}` |"
        )
    return "\n".join(lines)


def render_fix_plan(mode: str, parsed: dict[str, Any], kb_notes: dict[str, Any] | None) -> str:
    lines = [f"# {mode} Fix Plan", "", "This is a review plan, not an applied RTL patch.", ""]
    for rec in parsed["tags"]:
        tag = rec["tag"]
        example = rec.get("examples", [{}])[0] if rec.get("examples") else {}
        note = (kb_notes or {}).get(tag, {})
        lines.append(f"## {tag}")
        lines.append(f"- Count: {rec.get('count', 0)}")
        if example.get("filename"):
            loc = example.get("filename", "")
            if example.get("linenumber"):
                loc += f":{example['linenumber']}"
            lines.append(f"- Example: `{loc}`")
        if example.get("description"):
            lines.append(f"- Diagnostic: {example['description']}")
        if mode == "with-kb" and note:
            lines.append(f"- KB guidance: {note.get('summary', 'see cited context')}")
            if note.get("citation"):
                lines.append(f"- Citation: {note['citation']}")
        elif mode == "with-kb":
            lines.append("- KB guidance: not queried or no relevant hit recorded")
        else:
            lines.append("- No-KB heuristic: inspect the highlighted RTL, preserve behavior, prefer explicit width/reset/drive semantics, and avoid waivers unless reviewed.")
        lines.append("- Proposed action: manual review required before applying any RTL fix.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--mode", choices=["no-kb", "with-kb"], default="no-kb")
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--started-at", help="ISO timestamp. Defaults to current time when omitted.")
    ap.add_argument("--ended-at", help="ISO timestamp. Defaults to current time when omitted.")
    ap.add_argument("--kb-notes", type=Path, help="Optional JSON map: tag -> {summary,citation}")
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    parsed = parse_report(args.report)
    start = parse_time(args.started_at) or dt.datetime.now(dt.timezone.utc)
    end = parse_time(args.ended_at) or dt.datetime.now(dt.timezone.utc)
    elapsed = max(0.0, (end - start).total_seconds())
    kb_notes = load_json(args.kb_notes, {}) if args.kb_notes else {}

    history_path = args.outdir / "round_history.json"
    history = load_json(history_path, {"rounds": []})
    round_rec = {
        "mode": args.mode,
        "round": args.round,
        "started_at": start.isoformat(timespec="seconds"),
        "ended_at": end.isoformat(timespec="seconds"),
        "elapsed_seconds": elapsed,
        "report": str(args.report),
        "unique_tags": parsed["unique_tags"],
        "total_violations": parsed["total_violations"],
        "total_findings": parsed.get("total_findings", parsed["total_violations"]),
        "info_messages": parsed.get("info_messages", 0),
        "tag_names": [r["tag"] for r in parsed["tags"]],
    }
    history["rounds"] = [r for r in history["rounds"] if not (r["mode"] == args.mode and r["round"] == args.round)]
    history["rounds"].append(round_rec)
    history["rounds"].sort(key=lambda r: (r["mode"], r["round"]))

    (args.outdir / f"parsed_{args.mode}_round{args.round}.json").write_text(json.dumps(parsed, indent=2))
    history_path.write_text(json.dumps(history, indent=2))
    (args.outdir / "comparison.md").write_text("# Lint Autofix Comparison\n\n" + render_round_table(history["rounds"]) + "\n")
    (args.outdir / f"fix_plan_{args.mode}_round{args.round}.md").write_text(render_fix_plan(args.mode, parsed, kb_notes))
    print(json.dumps(round_rec, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
