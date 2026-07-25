from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_scope_guard.policy import (
    Policy,
    PolicyError,
    evaluate_paths,
    load_policy,
    normalize_changed_path,
)


class EvaluatePathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = Policy(
            allowed_paths=("agent_scope_guard/**", "tests/**", "README.md"),
            denied_paths=("**/*.key",),
            required_paths=("tests/**",),
        )

    def test_allowed_paths_pass(self) -> None:
        violations = evaluate_paths(
            self.policy,
            ["agent_scope_guard/cli.py", "tests/test_cli.py"],
        )
        self.assertEqual(violations, ())

    def test_outside_path_fails(self) -> None:
        violations = evaluate_paths(
            self.policy,
            ["private/customer.py", "tests/test_cli.py"],
        )
        self.assertEqual(violations[0].code, "outside_allowed_scope")
        self.assertEqual(violations[0].path, "private/customer.py")

    def test_denied_path_takes_priority(self) -> None:
        policy = Policy(
            allowed_paths=("**",),
            denied_paths=("**/*.key",),
        )
        for path in ("secrets/deploy.key", "deploy.key"):
            with self.subTest(path=path):
                violations = evaluate_paths(policy, [path])
                self.assertEqual(len(violations), 1)
                self.assertEqual(violations[0].code, "denied_path")

    def test_required_path_must_be_changed(self) -> None:
        violations = evaluate_paths(self.policy, ["agent_scope_guard/cli.py"])
        self.assertEqual(violations[-1].code, "required_path_missing")
        self.assertEqual(violations[-1].pattern, "tests/**")

    def test_windows_separator_is_normalized(self) -> None:
        violations = evaluate_paths(
            self.policy,
            [r"agent_scope_guard\cli.py", r"tests\test_cli.py"],
        )
        self.assertEqual(violations, ())

    def test_hidden_directory_name_is_preserved(self) -> None:
        policy = Policy(allowed_paths=(".github/**",))
        violations = evaluate_paths(policy, [".github/workflows/ci.yml"])
        self.assertEqual(violations, ())
        self.assertEqual(
            normalize_changed_path(".github/workflows/ci.yml"),
            ".github/workflows/ci.yml",
        )


class PolicyLoadingTests(unittest.TestCase):
    def test_loads_valid_policy(self) -> None:
        payload = {
            "allowed_paths": ["src/**"],
            "denied_paths": ["**/*.pem"],
            "required_paths": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "policy.json")
            path.write_text(json.dumps(payload), encoding="utf-8")
            policy = load_policy(path)
        self.assertEqual(policy.allowed_paths, ("src/**",))

    def test_unknown_field_is_rejected(self) -> None:
        payload = {"allowed_paths": ["src/**"], "allow_shell": True}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "policy.json")
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(PolicyError, "unknown policy field"):
                load_policy(path)

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaisesRegex(PolicyError, "escapes the repository"):
            normalize_changed_path("../company/private.py")


if __name__ == "__main__":
    unittest.main()
