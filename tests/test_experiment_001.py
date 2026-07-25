from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest


class Experiment001Tests(unittest.TestCase):
    def test_committed_result_matches_fresh_run(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        runner = repository_root / "experiments/001-scope-boundaries/run.py"
        result = subprocess.run(
            [sys.executable, str(runner), "--verify"],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("matches the committed evidence", result.stdout)


if __name__ == "__main__":
    unittest.main()
