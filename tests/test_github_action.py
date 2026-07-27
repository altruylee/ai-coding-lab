from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACTION_ENTRYPOINT = REPOSITORY_ROOT / "scripts" / "github_action.py"
ACTION_VERIFIER = REPOSITORY_ROOT / "scripts" / "verify_github_action.py"
ACTION_VARIABLES = {
    "AGENT_SCOPE_POLICY",
    "AGENT_SCOPE_BASE_REF",
    "AGENT_SCOPE_HEAD_REF",
    "AGENT_SCOPE_OUTPUT_FORMAT",
}


class GitHubActionTests(unittest.TestCase):
    def _environment(self, **values: str) -> dict[str, str]:
        environment = os.environ.copy()
        for name in ACTION_VARIABLES:
            environment.pop(name, None)
        environment.update(values)
        return environment

    def test_deterministic_integration_scenarios(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ACTION_VERIFIER)],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout,
            "github action integration scenarios passed\n",
        )

    def test_missing_policy_is_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(ACTION_ENTRYPOINT)],
                cwd=temporary,
                env=self._environment(AGENT_SCOPE_BASE_REF="HEAD^"),
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("policy input must not be empty", result.stderr)

    def test_invalid_output_format_is_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(ACTION_ENTRYPOINT)],
                cwd=temporary,
                env=self._environment(
                    AGENT_SCOPE_POLICY="policy.json",
                    AGENT_SCOPE_BASE_REF="HEAD^",
                    AGENT_SCOPE_OUTPUT_FORMAT="xml",
                ),
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("output_format must be text or json", result.stderr)

    def test_policy_path_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(ACTION_ENTRYPOINT)],
                cwd=temporary,
                env=self._environment(
                    AGENT_SCOPE_POLICY="../policy.json",
                    AGENT_SCOPE_BASE_REF="HEAD^",
                ),
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("policy input must stay inside the repository", result.stderr)

    def test_action_metadata_calls_checked_entrypoint(self) -> None:
        metadata = Path(REPOSITORY_ROOT, "action.yml").read_text(encoding="utf-8")
        self.assertIn("using: composite", metadata)
        self.assertIn('python "$GITHUB_ACTION_PATH/scripts/github_action.py"', metadata)
        for input_name in ("policy", "base_ref", "head_ref", "output_format"):
            self.assertIn(f"  {input_name}:", metadata)


if __name__ == "__main__":
    unittest.main()
