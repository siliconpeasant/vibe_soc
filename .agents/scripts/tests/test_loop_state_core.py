from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import loop_state_core as core  # noqa: E402


def write(path: Path, content: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class WorkspaceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / ".git").mkdir()
        self.workspace = self.repo / "ip" / "digital" / "demo"
        self.workspace.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def load(self) -> dict:
        return json.loads(
            (self.workspace / "pipeline_state.json").read_text(encoding="utf-8")
        )

    def init(self) -> dict:
        core.init_state_single(str(self.workspace), "demo")
        return self.load()

    def close_doc(self) -> None:
        core.update_state(str(self.workspace), "doc", "in_progress")
        write(self.workspace / "docs" / "design_spec.md", "# Design\n")
        core.update_state(
            str(self.workspace),
            "doc",
            "done",
            artifacts=["docs/design_spec.md"],
            checks=["doc_review:passed"],
        )

    def close_rtl(self) -> None:
        core.update_state(str(self.workspace), "rtl", "in_progress")
        write(self.workspace / "de" / "rtl" / "demo.sv", "module demo; endmodule\n")
        write(self.workspace / "de" / "rtl" / "filelist.f", "demo.sv\n")
        core.update_state(
            str(self.workspace),
            "rtl",
            "done",
            artifacts=["de/rtl/demo.sv", "de/rtl/filelist.f"],
            checks=[
                "soc_lint:passed",
                "soc_comp:passed",
                "rtl_quality:passed",
            ],
        )

    def test_init_is_schema_v3_and_repo_relative(self) -> None:
        state = self.init()
        self.assertEqual(state["schema_version"], 3)
        self.assertEqual(state["workspace"], "ip/digital/demo")
        self.assertEqual(state["pipeline"]["doc"]["status"], "pending")
        self.assertEqual(state["pipeline"]["rtl"]["status"], "blocked")
        self.assertFalse(core.state_errors(core.validate_state(state, self.workspace)))

    def test_required_checks_and_fail_note_are_enforced(self) -> None:
        self.init()
        core.update_state(str(self.workspace), "doc", "in_progress")
        write(self.workspace / "docs" / "design_spec.md", "# Design\n")
        with self.assertRaisesRegex(ValueError, "required checks"):
            core.update_state(
                str(self.workspace),
                "doc",
                "done",
                artifacts=["docs/design_spec.md"],
                checks=["unrelated:passed"],
            )
        with self.assertRaisesRegex(ValueError, "requires --note"):
            core.update_state(
                str(self.workspace),
                "doc",
                "fail",
                checks=["doc_completeness:failed"],
            )

    def test_artifact_root_is_enforced(self) -> None:
        self.init()
        core.update_state(str(self.workspace), "doc", "in_progress")
        write(self.workspace / "legacy" / "doc.md", "# Design\n")
        with self.assertRaisesRegex(ValueError, "outside approved roots"):
            core.update_state(
                str(self.workspace),
                "doc",
                "done",
                artifacts=["legacy/doc.md"],
                checks=["doc_completeness:passed"],
            )

    def test_rtl_checker_ignores_vendor_sdc_but_rejects_owned_sdc(self) -> None:
        write(self.workspace / "de" / "rtl" / "demo.sv", "module demo; endmodule\n")
        write(self.workspace / "de" / "rtl" / "filelist.f", "demo.sv\n")
        write(
            self.workspace / "de" / "rtl" / "vendor" / "upstream" / "constraints.sdc",
            "create_clock -period 10 clk\n",
        )
        clean = core._call_checker("rtl", self.workspace, "", {}, policy="review")
        self.assertTrue(clean["passed"], clean["issues"])
        write(
            self.workspace / "de" / "rtl" / "owned_constraints.sdc",
            "create_clock -period 10 clk\n",
        )
        misplaced = core._call_checker("rtl", self.workspace, "", {}, policy="review")
        self.assertFalse(misplaced["passed"])
        self.assertTrue(any("owned_constraints.sdc" in issue for issue in misplaced["issues"]))

    def test_downstream_evidence_is_bound_to_rtl_snapshot(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        core.update_state(str(self.workspace), "verif", "in_progress")
        write(self.workspace / "dv" / "tb" / "tb_demo.sv", "module tb_demo; endmodule\n")
        write(self.workspace / "dv" / "sim" / "sim.log", "RESULT: ALL TESTS PASS\n")
        fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "verif",
            "done",
            artifacts=["dv/tb/tb_demo.sv", "dv/sim/sim.log"],
            checks=["soc_sim:passed", "sim_log:passed"],
            source_fingerprint=fingerprint,
            run_id="soc_sim-test-snapshot",
        )
        state = self.load()
        rtl_fp = state["pipeline"]["rtl"]["rtl_fingerprint"]
        self.assertEqual(state["pipeline"]["verif"]["rtl_fingerprint"], rtl_fp)
        self.assertEqual(rtl_fp, core.compute_rtl_fingerprint(self.workspace))
        write(
            self.workspace / "de" / "rtl" / "demo.sv",
            "module demo; wire changed; endmodule\n",
        )
        issues = core.validate_state(state, self.workspace)
        self.assertTrue(
            any(issue.get("code") == "rtl_fingerprint_mismatch" or "stale" in issue["message"]
                for issue in issues)
        )

    def test_compact_summary_turns_invalid_evidence_into_next_action(self) -> None:
        self.init()
        self.close_doc()
        state = self.load()
        write(self.workspace / "docs" / "design_spec.md", "# Changed after review\n")
        issues = core.validate_state(state, self.workspace)
        summary = core.compact_state_summary(state, self.workspace, issues=issues)
        self.assertFalse(summary["valid"])
        repair = [
            action
            for action in summary["next_actions"]
            if action["stage"] == "doc" and action["action"] == "repair_evidence"
        ]
        self.assertEqual(len(repair), 1)
        self.assertIn("digest", repair[0]["reason"])

    def test_stale_mcp_source_fingerprint_cannot_close_verification(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        core.update_state(str(self.workspace), "verif", "in_progress")
        stale = core.compute_rtl_fingerprint(self.workspace)
        write(
            self.workspace / "de" / "rtl" / "demo.sv",
            "module demo; wire repaired; endmodule\n",
        )
        write(self.workspace / "dv" / "sim" / "sim.log", "RESULT: ALL TESTS PASS\n")
        with self.assertRaisesRegex(ValueError, "consumed source fingerprint"):
            core.update_state(
                str(self.workspace),
                "verif",
                "done",
                artifacts=["dv/sim/sim.log"],
                checks=["soc_sim:passed", "sim_log:passed"],
                source_fingerprint=stale,
                run_id="soc_sim-stale",
            )
        self.assertEqual(self.load()["pipeline"]["verif"]["status"], "in_progress")

    def test_resolved_child_ip_source_changes_top_fingerprint(self) -> None:
        top = self.repo / "chip" / "top"
        child = self.repo / "ip" / "digital" / "child" / "de" / "rtl"
        write(top / "de" / "rtl" / "filelist.f", "$SOC/ip/digital/child/de/rtl/child.sv\n")
        write(top / "de" / "run" / "rtl.f", "-f ../rtl/filelist.f\n")
        write(child / "child.sv", "module child; endmodule\n")
        before = core.compute_rtl_fingerprint(top)
        write(child / "child.sv", "module child; wire changed; endmodule\n")
        after = core.compute_rtl_fingerprint(top)
        self.assertIsNotNone(before)
        self.assertNotEqual(before, after)

    def test_generated_resolved_manifest_does_not_change_local_fingerprint(self) -> None:
        rtl = self.workspace / "de" / "rtl"
        write(rtl / "demo.sv", "module demo; endmodule\n")
        write(rtl / "filelist.f", "demo.sv\n")
        before = core.compute_rtl_fingerprint(self.workspace)

        write(
            self.workspace / "de" / "run" / "rtl.f",
            f"{rtl / 'demo.sv'}\n",
        )
        after = core.compute_rtl_fingerprint(self.workspace)

        self.assertIsNotNone(before)
        self.assertEqual(before, after)

    def test_legacy_generated_manifest_fingerprint_is_normalized(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        core.update_state(str(self.workspace), "verif", "in_progress")
        rtl = self.workspace / "de" / "rtl"
        write(
            self.workspace / "de" / "run" / "rtl.f",
            f"{rtl / 'demo.sv'}\n",
        )
        reported = core._compute_rtl_fingerprint(
            self.workspace, include_generated_manifest=True
        )
        current = core.compute_rtl_fingerprint(self.workspace)
        self.assertNotEqual(reported, current)
        write(self.workspace / "dv" / "sim" / "sim.log", "RESULT: ALL TESTS PASS\n")

        core.update_state(
            str(self.workspace),
            "verif",
            "done",
            artifacts=["dv/sim/sim.log"],
            checks=["soc_sim:passed", "sim_log:passed"],
            source_fingerprint=reported,
            run_id="soc_sim-legacy-fingerprint",
        )

        evidence = self.load()["pipeline"]["verif"]["run_evidence"]
        self.assertEqual(evidence["source_fingerprint"], current)
        self.assertEqual(evidence["reported_source_fingerprint"], reported)
        self.assertEqual(
            evidence["fingerprint_normalization"], "generated_manifest_v1"
        )

    def test_transient_digest_becomes_warning_on_clean_clone(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        core.update_state(str(self.workspace), "verif", "in_progress")
        write(self.workspace / "dv" / "tb" / "tb_demo.sv", "module tb_demo; endmodule\n")
        log = self.workspace / "dv" / "sim" / "sim.log"
        write(log, "RESULT: ALL TESTS PASS\n")
        fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "verif",
            "done",
            artifacts=["dv/tb/tb_demo.sv", "dv/sim/sim.log"],
            checks=["soc_sim:passed", "sim_log:passed"],
            source_fingerprint=fingerprint,
            run_id="soc_sim-transient",
        )
        state = self.load()
        log.unlink()
        issues = core.validate_state(state, self.workspace)
        matching = [
            issue
            for issue in issues
            if issue.get("code") == "transient_evidence_only"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]["severity"], "warning")
        self.assertFalse(
            any(
                issue["severity"] == "error" and "dv/sim/sim.log" in issue["message"]
                for issue in issues
            )
        )

    def test_legacy_normalization_marks_current_snapshot(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        state = self.load()
        state["schema_version"] = 2
        state["workspace"] = str(self.workspace)
        rtl = state["pipeline"]["rtl"]
        rtl.pop("rtl_fingerprint", None)
        rtl.pop("artifact_evidence", None)
        normalized, changes = core.normalize_legacy_state(state, self.workspace)
        self.assertEqual(normalized["schema_version"], 3)
        self.assertEqual(normalized["workspace"], "ip/digital/demo")
        self.assertEqual(
            normalized["pipeline"]["rtl"]["rtl_fingerprint_source"],
            "migration_current_snapshot",
        )
        self.assertEqual(
            normalized["pipeline"]["rtl"]["evidence_policy"], "legacy_compatible"
        )
        self.assertTrue(changes)

    def test_legacy_tool_suffix_and_doc_review_survive_migration(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        state = self.load()
        state["schema_version"] = 2
        state["workspace"] = str(self.workspace)
        state["pipeline"]["rtl"]["check_results"] = [
            result
            for result in state["pipeline"]["rtl"]["check_results"]
            if result["tool"] != "soc_lint"
        ]
        write(self.workspace / "dv" / "sim" / "sim.log", "RESULT: ALL TESTS PASS\n")
        state["pipeline"]["verif"].update(
            {
                "status": "done",
                "blocked_by": [],
                "artifacts": ["dv/sim/sim.log"],
                "check_results": [
                    {
                        "tool": "soc_sim_chip_sw_uart_smoketest",
                        "passed": True,
                        "note": "",
                    },
                    {"tool": "sim_log", "passed": True, "note": ""},
                ],
            }
        )
        migrated, changes, issues = core.migrate_state_data(state, self.workspace)
        self.assertFalse(core.state_errors(issues), issues)
        self.assertEqual(migrated["pipeline"]["doc"]["status"], "done")
        self.assertEqual(migrated["pipeline"]["rtl"]["status"], "done")
        self.assertEqual(migrated["pipeline"]["verif"]["status"], "done")
        self.assertEqual(
            migrated["pipeline"]["verif"]["run_evidence"]["tool_family"],
            "soc_sim_chip_sw_uart_smoketest",
        )
        self.assertTrue(changes)

        state_path = self.workspace / "pipeline_state.json"
        state_path.write_text(json.dumps(migrated), encoding="utf-8")
        core.update_state(str(self.workspace), "syn", "in_progress")
        write(self.workspace / "de" / "syn" / "demo_netlist.v", "module demo; endmodule\n")
        fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "syn",
            "done",
            artifacts=["de/syn/demo_netlist.v"],
            checks=["soc_syn:passed"],
            source_fingerprint=fingerprint,
            run_id="soc_syn-after-legacy-migration",
        )
        self.assertEqual(self.load()["pipeline"]["syn"]["status"], "done")

    def test_dry_run_migration_removes_release_and_downgrades_claims(self) -> None:
        pipeline = core.new_pipeline()
        pipeline["doc"].update(
            {
                "status": "done",
                "artifacts": ["docs/missing.md"],
                "check_results": [
                    {"tool": "doc_completeness", "passed": True, "note": ""}
                ],
                "blocked_by": [],
            }
        )
        pipeline["rtl"]["status"] = "pending"
        pipeline["rtl"]["blocked_by"] = []
        pipeline["release"] = {"status": "done", "artifacts": [], "check_results": []}
        legacy = {
            "mode": "single",
            "module": "demo",
            "workspace": str(self.workspace),
            "pipeline": pipeline,
        }
        state_path = self.workspace / "pipeline_state.json"
        state_path.write_text(json.dumps(legacy), encoding="utf-8")
        before = state_path.read_text(encoding="utf-8")
        result = core.migrate_state(str(self.workspace), write=False)
        self.assertEqual(state_path.read_text(encoding="utf-8"), before)
        migrated = result["state"]
        self.assertNotIn("release", migrated["pipeline"])
        self.assertEqual(migrated["pipeline"]["doc"]["status"], "pending")
        self.assertEqual(migrated["pipeline"]["rtl"]["status"], "blocked")
        self.assertFalse(core.state_errors(result["issues"]))

    def test_multi_module_issues_include_module(self) -> None:
        state = {
            "schema_version": 3,
            "ip": "bundle",
            "workspace": "ip/digital/demo",
            "mode": "multi_module",
            "created_at": core.now(),
            "last_updated": core.now(),
            "modules": {
                "good": {"pipeline": core.new_pipeline(), "next_actions": []},
                "bad": {"pipeline": core.new_pipeline(), "next_actions": []},
            },
        }
        state["modules"]["bad"]["pipeline"]["release"] = {"status": "done"}
        issues = core.validate_state(state, self.workspace, verify_filesystem=False)
        illegal = [issue for issue in issues if "illegal pipeline stage" in issue["message"]]
        self.assertEqual(illegal[0]["module"], "bad")

    def test_future_schema_is_rejected_without_rewrite(self) -> None:
        state = self.init()
        state["schema_version"] = 4
        path = self.workspace / "pipeline_state.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        before = path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsupported schema_version"):
            core.migrate_state(str(self.workspace), write=True)
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_active_state_migration_is_skipped_and_never_written(self) -> None:
        self.init()
        core.update_state(str(self.workspace), "doc", "in_progress")
        before = (self.workspace / "pipeline_state.json").read_text(encoding="utf-8")
        dry_run = core.migrate_state(str(self.workspace), write=False)
        self.assertTrue(dry_run["skipped"])
        with self.assertRaisesRegex(ValueError, "active stages"):
            core.migrate_state(str(self.workspace), write=True)
        self.assertEqual(
            (self.workspace / "pipeline_state.json").read_text(encoding="utf-8"),
            before,
        )

    def test_structural_synthesis_closes_without_fake_sta(self) -> None:
        self.init()
        self.close_doc()
        self.close_rtl()
        core.update_state(str(self.workspace), "syn", "in_progress")
        write(self.workspace / "de" / "syn" / "demo_netlist.v", "module demo; endmodule\n")
        write(self.workspace / "de" / "syn" / "synth.log", "synthesis complete\n")
        fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "syn",
            "done",
            artifacts=["de/syn/demo_netlist.v", "de/syn/synth.log"],
            checks=["soc_syn:passed"],
            source_fingerprint=fingerprint,
            run_id="soc_syn-structural-only",
        )
        syn = self.load()["pipeline"]["syn"]
        self.assertEqual(syn["status"], "done")
        self.assertFalse(any("timing" in item for item in syn["artifacts"]))

    def test_every_recorded_timing_report_must_pass(self) -> None:
        write(self.workspace / "de" / "syn" / "timing_fast.rpt", "WNS: 0.1\nTNS: 0.0\n")
        write(self.workspace / "de" / "syn" / "timing_slow.rpt", "WNS: -0.2\nTNS: -1.0\n")
        result = core._call_checker(
            "syn",
            self.workspace,
            "",
            {
                "artifacts": [
                    "de/syn/timing_fast.rpt",
                    "de/syn/timing_slow.rpt",
                ],
                "check_results": [{"tool": "timing", "passed": True}],
            },
            policy="closure",
        )
        self.assertFalse(result["passed"])
        self.assertTrue(any("timing_slow.rpt" in issue for issue in result["issues"]))

    def test_normal_review_invokes_all_done_stage_checkers(self) -> None:
        self.init()
        core.update_state(str(self.workspace), "doc", "in_progress")
        docs = [
            "design_spec.md",
            "interface_spec.md",
            "regmap.md",
            "verification_plan.md",
        ]
        for name in docs:
            write(self.workspace / "docs" / name, f"# {name}\n")
        core.update_state(
            str(self.workspace),
            "doc",
            "done",
            artifacts=[f"docs/{name}" for name in docs],
            checks=["doc_completeness:passed"],
        )
        self.close_rtl()
        core.update_state(str(self.workspace), "verif", "in_progress")
        write(self.workspace / "dv" / "tb" / "tb_demo.sv", "module tb_demo; endmodule\n")
        write(self.workspace / "dv" / "sim" / "sim.log", "RESULT: ALL TESTS PASS\n")
        verif_fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "verif",
            "done",
            artifacts=["dv/tb/tb_demo.sv", "dv/sim/sim.log"],
            checks=["soc_sim:passed", "sim_log:passed"],
            source_fingerprint=verif_fingerprint,
            run_id="soc_sim-normal-review",
        )
        core.update_state(str(self.workspace), "syn", "in_progress")
        write(self.workspace / "de" / "syn" / "demo_netlist.v", "module demo; endmodule\n")
        write(self.workspace / "de" / "syn" / "synth.log", "synthesis complete\n")
        write(self.workspace / "de" / "syn" / "demo.sdc", "create_clock -period 10 clk\n")
        write(self.workspace / "de" / "syn" / "timing.rpt", "WNS: 0.10\nTNS: 0.00\n")
        syn_fingerprint = core.compute_rtl_fingerprint(self.workspace)
        core.update_state(
            str(self.workspace),
            "syn",
            "done",
            artifacts=[
                "de/syn/demo_netlist.v",
                "de/syn/synth.log",
                "de/syn/demo.sdc",
                "de/syn/timing.rpt",
            ],
            checks=["soc_syn:passed", "timing:passed"],
            source_fingerprint=syn_fingerprint,
            run_id="soc_syn-normal-review",
        )
        result = core.check(str(self.workspace), "normal")
        self.assertEqual(result["outcome"], "pass", result["issues"])
        # formal/integrate remain pending unless closed or skipped; evidence
        # report lists stages that recorded checks in this review path.
        self.assertTrue(
            {"doc", "rtl", "verif", "syn"}.issubset(
                set(result["details"]["evidence_checks"]["demo"])
            )
        )

    def _handoff_pack(self, *, netlist: str, formal: str, note: str) -> dict:
        write(self.workspace / "de" / "rtl" / "filelist.f", "demo.sv\n")
        write(self.workspace / "de" / "syn" / "demo_netlist.v", netlist)
        write(self.workspace / "de" / "syn" / "demo.sdc", "create_clock -period 10 clk\n")
        write(
            self.workspace / "de" / "run" / "formality" / "verification_status.rpt",
            formal,
        )
        write(self.workspace / "docs" / "frontend_handoff.md", note)
        return {
            "artifacts": [
                "de/rtl/filelist.f",
                "de/syn/demo_netlist.v",
                "de/syn/demo.sdc",
                "de/run/formality/verification_status.rpt",
                "docs/frontend_handoff.md",
            ]
        }

    def test_handoff_checker_requires_nonempty_netlist_and_formal_succeeded(self) -> None:
        empty_netlist = self._handoff_pack(
            netlist="",
            formal="VERIFICATION_STATUS=SUCCEEDED\n",
            note="# frontend handoff\nNot timing closure.\n",
        )
        empty_result = core._call_checker(
            "handoff", self.workspace, "", empty_netlist, policy="closure"
        )
        self.assertFalse(empty_result["passed"])
        self.assertTrue(
            any("empty" in issue and "netlist" in issue for issue in empty_result["issues"])
        )

        failed_formal = self._handoff_pack(
            netlist="module demo; endmodule\n",
            formal="VERIFICATION_STATUS=FAILED\n",
            note="# frontend handoff\nNot timing closure.\n",
        )
        failed_result = core._call_checker(
            "handoff", self.workspace, "", failed_formal, policy="closure"
        )
        self.assertFalse(failed_result["passed"])
        self.assertTrue(
            any("SUCCEEDED" in issue for issue in failed_result["issues"])
        )

        good = self._handoff_pack(
            netlist="module demo; endmodule\n",
            formal="Status:             SUCCEEDED\nVERIFICATION_STATUS=SUCCEEDED\n",
            note="# frontend handoff\nNot timing closure.\n",
        )
        good_result = core._call_checker(
            "handoff", self.workspace, "", good, policy="closure"
        )
        self.assertTrue(good_result["passed"], good_result["issues"])


if __name__ == "__main__":
    unittest.main()
