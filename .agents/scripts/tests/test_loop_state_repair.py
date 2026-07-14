from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import loop_state_core as core  # noqa: E402


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class DownstreamRepairTest(unittest.TestCase):
    def _closed_rtl_workspace(self, repo: Path) -> Path:
        (repo / ".git").mkdir()
        workspace = repo / "ip" / "demo"
        workspace.mkdir(parents=True)
        core.init_state_single(str(workspace), "demo")
        core.update_state(str(workspace), "doc", "in_progress")
        write(workspace / "docs" / "d.md", "# d\n")
        core.update_state(
            str(workspace),
            "doc",
            "done",
            artifacts=["docs/d.md"],
            checks=["doc_review:passed"],
        )
        core.update_state(str(workspace), "rtl", "in_progress")
        write(workspace / "de" / "rtl" / "d.sv", "module d; endmodule\n")
        write(workspace / "de" / "rtl" / "filelist.f", "d.sv\n")
        core.update_state(
            str(workspace),
            "rtl",
            "done",
            artifacts=["de/rtl/d.sv", "de/rtl/filelist.f"],
            checks=[
                "soc_lint:passed",
                "soc_comp:passed",
                "rtl_quality:passed",
            ],
        )
        return workspace

    def test_current_schema_migration_invalidates_stale_downstream_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = self._closed_rtl_workspace(Path(temp))
            fingerprint = core.compute_rtl_fingerprint(workspace)

            core.update_state(str(workspace), "verif", "in_progress")
            write(workspace / "dv/tb/tb_d.sv", "module tb_d; endmodule\n")
            write(workspace / "dv/sim/sim.log", "RESULT: ALL TESTS PASS\n")
            core.update_state(
                str(workspace),
                "verif",
                "done",
                artifacts=["dv/tb/tb_d.sv", "dv/sim/sim.log"],
                checks=["soc_sim:passed", "sim_log:passed"],
                source_fingerprint=fingerprint,
                run_id="soc_sim-before-drift",
            )
            core.update_state(str(workspace), "syn", "in_progress")
            write(workspace / "de/syn/d_netlist.v", "module d; endmodule\n")
            write(workspace / "de/syn/synth.log", "synthesis completed\n")
            core.update_state(
                str(workspace),
                "syn",
                "done",
                artifacts=["de/syn/d_netlist.v", "de/syn/synth.log"],
                checks=["soc_syn:passed"],
                source_fingerprint=fingerprint,
                run_id="soc_syn-before-drift",
            )

            state = json.loads(
                (workspace / "pipeline_state.json").read_text(encoding="utf-8")
            )
            stale_fingerprint = "0" * 64
            for stage in ("verif", "syn"):
                state["pipeline"][stage]["rtl_fingerprint"] = stale_fingerprint
                state["pipeline"][stage]["run_evidence"][
                    "source_fingerprint"
                ] = stale_fingerprint
            migrated, changes, issues = core.migrate_state_data(state, workspace)

            self.assertFalse(core.state_errors(issues))
            self.assertEqual(migrated["pipeline"]["doc"]["status"], "done")
            self.assertEqual(migrated["pipeline"]["rtl"]["status"], "done")
            self.assertEqual(migrated["pipeline"]["verif"]["status"], "pending")
            self.assertEqual(migrated["pipeline"]["syn"]["status"], "pending")
            self.assertIn("demo/verif: done -> pending", changes)
            self.assertIn("demo/syn: done -> pending", changes)

    def test_current_schema_migration_preserves_valid_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = self._closed_rtl_workspace(Path(temp))
            fingerprint = core.compute_rtl_fingerprint(workspace)

            core.update_state(str(workspace), "verif", "in_progress")
            write(workspace / "dv/tb/tb_d.sv", "module tb_d; endmodule\n")
            write(workspace / "dv/sim/sim.log", "RESULT: ALL TESTS PASS\n")
            core.update_state(
                str(workspace),
                "verif",
                "done",
                artifacts=["dv/tb/tb_d.sv", "dv/sim/sim.log"],
                checks=["soc_sim:passed", "sim_log:passed"],
                source_fingerprint=fingerprint,
                run_id="soc_sim-valid-v3",
            )
            core.update_state(str(workspace), "syn", "in_progress")
            write(workspace / "de/syn/d_netlist.v", "module d; endmodule\n")
            write(workspace / "de/syn/synth.log", "synthesis completed\n")
            core.update_state(
                str(workspace),
                "syn",
                "done",
                artifacts=["de/syn/d_netlist.v", "de/syn/synth.log"],
                checks=["soc_syn:passed"],
                source_fingerprint=fingerprint,
                run_id="soc_syn-valid-v3",
            )

            state = json.loads(
                (workspace / "pipeline_state.json").read_text(encoding="utf-8")
            )
            migrated, changes, issues = core.migrate_state_data(state, workspace)

            self.assertEqual(changes, [])
            self.assertFalse(core.state_errors(issues))
            self.assertEqual(migrated, state)
            self.assertEqual(
                migrated["pipeline"]["verif"]["run_evidence"]["run_id"],
                "soc_sim-valid-v3",
            )
            self.assertEqual(
                migrated["pipeline"]["syn"]["run_evidence"]["run_id"],
                "soc_syn-valid-v3",
            )

    def test_verification_repair_can_close_and_invalidates_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / ".git").mkdir()
            workspace = repo / "ip" / "demo"
            workspace.mkdir(parents=True)
            core.init_state_single(str(workspace), "demo")

            core.update_state(str(workspace), "doc", "in_progress")
            write(workspace / "docs" / "d.md", "# d\n")
            core.update_state(
                str(workspace),
                "doc",
                "done",
                artifacts=["docs/d.md"],
                checks=["doc_review:passed"],
            )
            core.update_state(str(workspace), "rtl", "in_progress")
            write(workspace / "de" / "rtl" / "d.sv", "module d; endmodule\n")
            write(workspace / "de" / "rtl" / "filelist.f", "d.sv\n")
            core.update_state(
                str(workspace),
                "rtl",
                "done",
                artifacts=["de/rtl/d.sv", "de/rtl/filelist.f"],
                checks=[
                    "soc_lint:passed",
                    "soc_comp:passed",
                    "rtl_quality:passed",
                ],
            )

            core.update_state(str(workspace), "syn", "in_progress")
            write(
                workspace / "de" / "syn" / "d_netlist.v",
                "module d; endmodule\n",
            )
            write(workspace / "de" / "syn" / "timing.rpt", "WNS: 0.1\nTNS: 0.0\n")
            syn_fingerprint = core.compute_rtl_fingerprint(workspace)
            core.update_state(
                str(workspace),
                "syn",
                "done",
                artifacts=["de/syn/d_netlist.v", "de/syn/timing.rpt"],
                checks=["soc_syn:passed", "timing:passed"],
                source_fingerprint=syn_fingerprint,
                run_id="soc_syn-before-repair",
            )

            core.update_state(str(workspace), "verif", "in_progress")
            write(
                workspace / "de" / "rtl" / "d.sv",
                "module d; wire repaired; endmodule\n",
            )
            write(workspace / "dv" / "tb" / "tb.sv", "module tb; endmodule\n")
            write(
                workspace / "dv" / "sim" / "sim.log",
                "RESULT: ALL TESTS PASS\n",
            )
            repaired_fingerprint = core.compute_rtl_fingerprint(workspace)
            core.update_state(
                str(workspace),
                "verif",
                "done",
                artifacts=["dv/tb/tb.sv", "dv/sim/sim.log"],
                checks=[
                    "soc_sim:passed",
                    "sim_log:passed",
                    "soc_lint:passed",
                    "soc_comp:passed",
                    "rtl_quality:passed",
                ],
                source_fingerprint=repaired_fingerprint,
                run_id="soc_sim-after-repair",
            )

            state = json.loads(
                (workspace / "pipeline_state.json").read_text(encoding="utf-8")
            )
            pipeline = state["pipeline"]
            current = core.compute_rtl_fingerprint(workspace)
            self.assertEqual(pipeline["rtl"]["rtl_fingerprint"], current)
            self.assertEqual(pipeline["verif"]["rtl_fingerprint"], current)
            self.assertEqual(pipeline["syn"]["status"], "pending")
            self.assertIn("rerun required", pipeline["syn"]["notes"])
            self.assertFalse(
                core.state_errors(core.validate_state(state, workspace))
            )

    def test_failed_downstream_repair_is_recorded_and_reopens_rtl(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = self._closed_rtl_workspace(Path(temp))
            core.update_state(str(workspace), "verif", "in_progress")
            write(
                workspace / "de" / "rtl" / "d.sv",
                "module d; wire broken_repair; endmodule\n",
            )
            core.update_state(
                str(workspace),
                "verif",
                "fail",
                checks=["soc_sim:failed:compile failed"],
                note="Repair did not pass simulation; return to RTL checks",
            )
            state = json.loads(
                (workspace / "pipeline_state.json").read_text(encoding="utf-8")
            )
            pipeline = state["pipeline"]
            self.assertEqual(pipeline["rtl"]["status"], "in_progress")
            self.assertEqual(pipeline["verif"]["status"], "fail")
            self.assertEqual(pipeline["verif"]["blocked_by"], ["rtl"])
            self.assertEqual(pipeline["syn"]["status"], "blocked")
            self.assertFalse(core.state_errors(core.validate_state(state, workspace)))

    def test_aborted_downstream_repair_invalidates_both_consumers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = self._closed_rtl_workspace(Path(temp))
            core.update_state(str(workspace), "verif", "in_progress")
            write(
                workspace / "de" / "rtl" / "d.sv",
                "module d; wire abandoned_repair; endmodule\n",
            )
            core.update_state(
                str(workspace),
                "verif",
                "pending",
                note="Abort verification repair and return to RTL review",
            )
            state = json.loads(
                (workspace / "pipeline_state.json").read_text(encoding="utf-8")
            )
            pipeline = state["pipeline"]
            self.assertEqual(pipeline["rtl"]["status"], "in_progress")
            self.assertEqual(pipeline["verif"]["status"], "blocked")
            self.assertEqual(pipeline["syn"]["status"], "blocked")
            self.assertFalse(core.state_errors(core.validate_state(state, workspace)))


if __name__ == "__main__":
    unittest.main()
