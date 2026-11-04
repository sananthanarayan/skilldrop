import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SmokeTest(unittest.TestCase):
    def test_runs_and_writes_trailer(self):
        out = subprocess.run(
            [sys.executable, str(ROOT / "legacy" / "feecalc.py"),
             str(ROOT / "samples" / "accounts_2026-10.txt"), "20261031"],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertTrue(out.startswith("# FEERUN 20261031"))
        self.assertIn("# TOTAL", out.splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
