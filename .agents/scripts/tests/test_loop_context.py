from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import loop_context  # noqa: E402
import loop_state_core as core  # noqa: E402


def write(path: Path, content: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class LoopContextCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "config", "user.email", "loop-test@example.invalid"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Loop Test"],
            cwd=self.repo,
            check=True,
        )
        self.workspace = self.repo / "ip" / "digital" / "demo"
        write(
            self.workspace / "de" / "rtl" / "demo.sv",
            "module demo(input logic data_i, output logic data_o);\n"
            "  assign data_o = data_i;\n"
            "endmodule\n",
        )
        write(self.workspace / "de" / "rtl" / "filelist.f", "demo.sv\n")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.repo, check=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def context(
        self,
        paths: list[str],
        *,
        mode: str = "dev",
        impacts: set[str] | None = None,
        review_result: str | None = None,
        risk_checks_passed: bool = False,
    ) -> dict:
        return loop_context.build_context(
            self.workspace,
            requested_mode=mode,
            base_ref="HEAD",
            changed_paths=paths,
            impacts=impacts or set(),
            review_result=review_result,
            risk_checks_passed=risk_checks_passed,
        )

    def test_low_risk_single_module_rtl_uses_dev(self) -> None:
        result = self.context(["ip/digital/demo/de/rtl/demo.sv"])
        self.assertEqual(result["mode"], "dev")
        self.assertTrue(result["pipeline_governed"])
        self.assertFalse(result["close_pipeline"])
        self.assertEqual(result["review_mode"], "not_run")
        self.assertNotIn("soc_syn", result["required_checks"])
        self.assertLess(len(json.dumps(result)), 4096)

    def test_filelist_escalates_to_merge(self) -> None:
        result = self.context(["ip/digital/demo/de/rtl/filelist.f"])
        self.assertEqual(result["mode"], "merge")
        self.assertIn("soc_syn", result["required_checks"])
        self.assertEqual(result["review_mode"], "normal")

    def test_constraint_and_explicit_interface_impact_escalate_to_signoff(self) -> None:
        constraint = self.context(["ip/digital/demo/de/syn/demo.sdc"])
        interface_doc = self.context(["ip/digital/demo/docs/interface_spec.md"])
        explicit = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"], impacts={"interface"}
        )
        self.assertEqual(constraint["mode"], "signoff")
        self.assertEqual(interface_doc["mode"], "signoff")
        self.assertEqual(explicit["mode"], "signoff")
        self.assertEqual(explicit["review_mode"], "strict")

    def test_port_declaration_diff_is_detected_as_interface_change(self) -> None:
        write(
            self.workspace / "de" / "rtl" / "demo.sv",
            "module demo(input logic data_i, output logic [1:0] data_o);\n"
            "  assign data_o = {2{data_i}};\n"
            "endmodule\n",
        )
        result = self.context(["ip/digital/demo/de/rtl/demo.sv"])
        self.assertEqual(result["mode"], "signoff")
        self.assertIn("interface", result["detected_impacts"])

    def test_new_module_and_multiple_workspaces_escalate_to_signoff(self) -> None:
        new_rtl = self.workspace / "de" / "rtl" / "new_unit.sv"
        write(new_rtl, "module new_unit(input logic a); endmodule\n")
        new_module = self.context(["ip/digital/demo/de/rtl/new_unit.sv"])
        multi = self.context(
            [
                "ip/digital/demo/de/rtl/demo.sv",
                "ip/digital/other/de/rtl/other.sv",
            ]
        )
        self.assertEqual(new_module["mode"], "signoff")
        self.assertIn("interface", new_module["detected_impacts"])
        self.assertEqual(multi["mode"], "signoff")

    def test_requested_mode_is_a_floor(self) -> None:
        result = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"], mode="merge"
        )
        self.assertEqual(result["mode"], "merge")

    def test_loop_mode_environment_sets_the_floor_for_auto(self) -> None:
        with patch.dict("os.environ", {"LOOP_MODE": "merge"}):
            result = loop_context.build_context(
                self.workspace,
                requested_mode="auto",
                base_ref="HEAD",
                changed_paths=["ip/digital/demo/de/rtl/demo.sv"],
            )
        self.assertEqual(result["mode"], "merge")

    def test_non_pipeline_change_uses_non_eda_validation(self) -> None:
        result = self.context(["README.md"])
        self.assertFalse(result["pipeline_governed"])
        self.assertEqual(result["required_checks"], ["closest_non_eda_validation"])
        self.assertEqual(result["rules"], [])
        self.assertEqual(result["cache"]["stages"], {})
        self.assertTrue(result["delivery_ready"])

    def test_documentation_inner_loop_does_not_open_rtl(self) -> None:
        result = self.context(["ip/digital/demo/docs/design_spec.md"])
        self.assertEqual(result["mode"], "dev")
        self.assertEqual(result["affected_stages"], ["doc"])
        self.assertEqual(result["required_checks"], ["doc_delta"])
        self.assertEqual(result["rules"], [".agents/rules/00_loop_modes.md"])
        self.assertIn("start or keep doc in_progress", result["next_actions"])

    def test_write_uses_module_de_run_and_refuses_repo_root(self) -> None:
        module_args = [
            "loop_context.py",
            str(self.workspace),
            "--base-ref",
            "HEAD",
            "--changed",
            "ip/digital/demo/de/rtl/demo.sv",
            "--write",
        ]
        with patch.object(sys, "argv", module_args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(loop_context.main(), 0)
        self.assertTrue(
            (self.workspace / "de/run/loop_evidence/loop_context.json").is_file()
        )

        root_args = [
            "loop_context.py",
            str(self.repo),
            "--base-ref",
            "HEAD",
            "--changed",
            "README.md",
            "--write",
        ]
        with (
            patch.object(sys, "argv", root_args),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(loop_context.main(), 1)
        self.assertFalse((self.repo / "de").exists())

    def close_pipeline(self) -> None:
        core.init_state_single(str(self.workspace), "demo")
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
        core.update_state(str(self.workspace), "rtl", "in_progress")
        core.update_state(
            str(self.workspace),
            "rtl",
            "done",
            artifacts=["de/rtl/demo.sv", "de/rtl/filelist.f"],
            checks=["soc_lint:passed", "soc_comp:passed", "rtl_quality:passed"],
        )
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
            run_id="soc_sim-loop-context",
        )
        core.update_state(str(self.workspace), "syn", "in_progress")
        write(self.workspace / "de" / "syn" / "demo_netlist.v", "module demo; endmodule\n")
        write(self.workspace / "de" / "syn" / "synth.log", "synthesis complete\n")
        core.update_state(
            str(self.workspace),
            "syn",
            "done",
            artifacts=["de/syn/demo_netlist.v", "de/syn/synth.log"],
            checks=["soc_syn:passed"],
            source_fingerprint=fingerprint,
            run_id="soc_syn-loop-context",
        )

    def test_final_evidence_reuses_current_fingerprint(self) -> None:
        self.close_pipeline()
        before_review = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"], mode="merge"
        )
        result = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"],
            mode="merge",
            review_result="pass",
        )
        self.assertTrue(before_review["stage_evidence_ready"])
        self.assertFalse(before_review["delivery_ready"])
        self.assertEqual(before_review["checks_to_run"], ["loop_review_normal"])
        self.assertTrue(result["delivery_ready"], result)
        self.assertEqual(result["checks_to_run"], [])
        self.assertLess(len(json.dumps(result)), 4096)
        self.assertTrue(
            all(item["fresh"] for item in result["cache"]["stages"].values())
        )

    def test_query_state_compact_omits_evidence_payloads(self) -> None:
        self.close_pipeline()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = core.query_state(str(self.workspace), compact=True)
        summary = json.loads(output.getvalue())
        self.assertTrue(result["valid"])
        self.assertTrue(summary["valid"])
        self.assertEqual(summary["stages"]["syn"]["status"], "done")
        self.assertNotIn("artifact_evidence", output.getvalue())
        self.assertNotIn("check_results", output.getvalue())
        self.assertLess(len(output.getvalue()), 4096)

    def test_signoff_requires_risk_checks_and_review(self) -> None:
        self.close_pipeline()
        pending = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"],
            impacts={"interface"},
            review_result="pass",
        )
        ready = self.context(
            ["ip/digital/demo/de/rtl/demo.sv"],
            impacts={"interface"},
            review_result="pass",
            risk_checks_passed=True,
        )
        self.assertTrue(pending["stage_evidence_ready"])
        self.assertFalse(pending["delivery_ready"])
        self.assertIn("risk_specific_checks", pending["checks_to_run"])
        self.assertTrue(ready["delivery_ready"])
        self.assertEqual(ready["checks_to_run"], [])


if __name__ == "__main__":
    unittest.main()
