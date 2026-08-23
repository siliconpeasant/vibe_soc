from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dft_gen.py"
TEMPLATE = ROOT / "references" / "dft_sgdc_template.yml"


class DftGenTest(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_from_rtl_and_readiness(self) -> None:
        rtl = """
module dft_demo (
  input  wire clk,
  input  wire rst_n,
  input  wire test_mode,
  input  wire test_rst_n,
  input  wire scan_en,
  input  wire [7:0] data_i,
  output wire [7:0] data_o
);
  assign data_o = data_i;
endmodule
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rtl_path = tmp_path / "dft_demo.v"
            rtl_path.write_text(rtl, encoding="utf-8")
            sgdc = tmp_path / "dft_demo_dft.sgdc"
            tcl = tmp_path / "dft_demo_dft.tcl"
            readiness = tmp_path / "ready.json"

            gen = self._run(
                "from-rtl",
                "--rtl",
                str(rtl_path),
                "-o",
                str(sgdc),
                "--tcl",
                str(tcl),
            )
            self.assertEqual(gen.returncode, 0, gen.stdout + gen.stderr)
            self.assertTrue(sgdc.is_file())
            text = sgdc.read_text(encoding="utf-8")
            self.assertIn("current_design dft_demo", text)
            self.assertIn("test_mode -name test_mode -value 1", text)
            self.assertIn("reset -name rst_n -value 0", text)
            self.assertIn("reset -name test_rst_n -value 0", text)
            self.assertIn("clock -name clk", text)
            self.assertIn("DFT_ARTIFACTS=", gen.stdout)
            self.assertTrue(tcl.is_file())
            self.assertIn("dft/dft_scan_ready", tcl.read_text(encoding="utf-8"))

            ready = self._run(
                "readiness",
                "--rtl",
                str(rtl_path),
                "--out",
                str(readiness),
                "--soft-scan",
            )
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
            report = json.loads(readiness.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["module"], "dft_demo")

    def test_gen_from_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "example_top_dft.sgdc"
            completed = self._run(
                "gen",
                "--config",
                str(TEMPLATE),
                "-o",
                str(out),
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            text = out.read_text(encoding="utf-8")
            self.assertIn("current_design example_top", text)
            self.assertIn("test_mode -name test_mode", text)

    def test_readiness_fail_without_test_mode(self) -> None:
        rtl = """
module plain (
  input wire clk,
  input wire rst_n,
  input wire d,
  output reg q
);
  always @(posedge clk or negedge rst_n)
    if (!rst_n) q <= 1'b0;
    else q <= d;
endmodule
"""
        with tempfile.TemporaryDirectory() as tmp:
            rtl_path = Path(tmp) / "plain.v"
            rtl_path.write_text(rtl, encoding="utf-8")
            out = Path(tmp) / "ready.json"
            completed = self._run(
                "readiness",
                "--rtl",
                str(rtl_path),
                "--out",
                str(out),
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "fail")
            self.assertIn("test_mode", report["must_missing"])


if __name__ == "__main__":
    unittest.main()
