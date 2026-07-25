from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def _run_cli(self, policy: dict[str, object], *paths: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            policy_path = Path(directory, "policy.json")
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            command = [
                sys.executable,
                "-m",
                "agent_scope_guard",
                "check",
                "--policy",
                str(policy_path),
                "--format",
                "json",
            ]
            for path in paths:
                command.extend(["--changed-path", path])
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

    def test_cli_returns_zero_for_allowed_change(self) -> None:
        result = self._run_cli(
            {"allowed_paths": ["src/**"], "required_paths": ["src/**"]},
            "src/app.py",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_cli_returns_one_for_scope_violation(self) -> None:
        result = self._run_cli(
            {"allowed_paths": ["src/**"]},
            "infra/production.yml",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(
            payload["violations"][0]["code"],
            "outside_allowed_scope",
        )

    def test_cli_returns_two_for_invalid_policy(self) -> None:
        result = self._run_cli({"allowed_paths": []}, "src/app.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("configuration error", result.stderr)


if __name__ == "__main__":
    unittest.main()
