from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_scope_guard.pre_commit import main


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class PreCommitHookTests(unittest.TestCase):
    def _run_hook(
        self,
        policy: dict[str, object],
        *filenames: str,
    ) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            policy_path = directory / "policy.json"
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            stdout = StringIO()
            stderr = StringIO()
            with (
                patch("agent_scope_guard.pre_commit.Path.is_absolute", return_value=False),
                patch("agent_scope_guard.pre_commit.load_policy") as load_policy,
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                from agent_scope_guard.policy import policy_from_mapping

                load_policy.return_value = policy_from_mapping(policy)
                exit_code = main(
                    [
                        "--policy",
                        "policy.json",
                        "--format",
                        "json",
                        *filenames,
                    ]
                )
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_allowed_staged_paths_pass(self) -> None:
        exit_code, stdout, stderr = self._run_hook(
            {
                "allowed_paths": ["src/**", "tests/**"],
                "required_paths": ["tests/**"],
            },
            "src/app.py",
            "tests/test_app.py",
        )
        self.assertEqual(exit_code, 0, stderr)
        self.assertTrue(json.loads(stdout)["ok"])

    def test_denied_staged_path_fails(self) -> None:
        exit_code, stdout, stderr = self._run_hook(
            {"allowed_paths": ["**"], "denied_paths": ["**/*.key"]},
            "deploy.key",
        )
        self.assertEqual(exit_code, 1, stderr)
        self.assertEqual(
            json.loads(stdout)["violations"][0]["code"],
            "denied_path",
        )

    def test_required_staged_path_must_be_present(self) -> None:
        exit_code, stdout, stderr = self._run_hook(
            {
                "allowed_paths": ["src/**", "tests/**"],
                "required_paths": ["tests/**"],
            },
            "src/app.py",
        )
        self.assertEqual(exit_code, 1, stderr)
        codes = {
            violation["code"]
            for violation in json.loads(stdout)["violations"]
        }
        self.assertIn("required_path_missing", codes)

    def test_policy_path_cannot_escape_repository(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--policy", "../policy.json", "src/app.py"])
        self.assertEqual(exit_code, 2)
        self.assertIn("must stay inside the repository", stderr.getvalue())

    def test_hook_manifest_and_console_entry_are_published(self) -> None:
        manifest = Path(REPOSITORY_ROOT, ".pre-commit-hooks.yaml").read_text(
            encoding="utf-8"
        )
        project = Path(REPOSITORY_ROOT, "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn("id: agent-scope-guard", manifest)
        self.assertIn("entry: agent-scope-guard-pre-commit", manifest)
        self.assertIn(
            'agent-scope-guard-pre-commit = "agent_scope_guard.pre_commit:main"',
            project,
        )


if __name__ == "__main__":
    unittest.main()
