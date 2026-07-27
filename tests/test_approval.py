from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from agent_scope_guard.approval import (
    ApprovalError,
    ApprovalRejected,
    build_proposal,
    load_proposal,
    serialize_proposal,
    validate_environment_snapshot,
    verify_proposal,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _repository() -> tuple[tempfile.TemporaryDirectory[str], Path, str, str]:
    temporary = tempfile.TemporaryDirectory()
    root = Path(temporary.name)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "approval@example.invalid")
    _git(root, "config", "user.name", "Approval Test")
    (root / "policy.json").write_text(
        json.dumps(
            {
                "allowed_paths": ["src/**", "tests/**"],
                "denied_paths": ["**/*.key"],
                "required_paths": ["tests/**"],
            }
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text("initial\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "initial")
    base = _git(root, "rev-parse", "HEAD")

    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
    (root / "tests" / "test_app.py").write_text(
        "def test_value(): pass\n",
        encoding="utf-8",
    )
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "agent change")
    head = _git(root, "rev-parse", "HEAD")
    return temporary, root, base, head


class ApprovalProposalTests(unittest.TestCase):
    def test_proposal_is_deterministic_and_verifiable(self) -> None:
        temporary, root, base, head = _repository()
        self.addCleanup(temporary.cleanup)

        first = build_proposal(root, "policy.json", base, head)
        second = build_proposal(root, "policy.json", base, head)
        proposal_path = root / "proposal.json"
        proposal_path.write_text(serialize_proposal(first), encoding="utf-8")

        self.assertEqual(first, second)
        self.assertEqual(
            first["changed_paths"],
            ["src/app.py", "tests/test_app.py"],
        )
        self.assertEqual(
            verify_proposal(
                proposal_path,
                root,
                "policy.json",
                base,
                head,
            ),
            first,
        )

    def test_tampered_proposal_digest_is_rejected(self) -> None:
        temporary, root, base, head = _repository()
        self.addCleanup(temporary.cleanup)
        proposal = build_proposal(root, "policy.json", base, head)
        proposal["changed_paths"] = ["src/other.py", "tests/test_app.py"]
        proposal_path = root / "proposal.json"
        proposal_path.write_text(serialize_proposal(proposal), encoding="utf-8")

        with self.assertRaisesRegex(ApprovalRejected, "digest"):
            load_proposal(proposal_path)

    def test_moving_head_ref_after_review_is_rejected(self) -> None:
        temporary, root, base, _ = _repository()
        self.addCleanup(temporary.cleanup)
        proposal = build_proposal(root, "policy.json", base, "HEAD")
        proposal_path = root / "proposal.json"
        proposal_path.write_text(serialize_proposal(proposal), encoding="utf-8")

        (root / "src" / "app.py").write_text("value = 2\n", encoding="utf-8")
        _git(root, "add", "src/app.py")
        _git(root, "commit", "-qm", "move head")

        with self.assertRaisesRegex(ApprovalRejected, "no longer matches"):
            verify_proposal(
                proposal_path,
                root,
                "policy.json",
                base,
                "HEAD",
            )

    def test_scope_violation_creates_no_approvable_proposal(self) -> None:
        temporary, root, base, _ = _repository()
        self.addCleanup(temporary.cleanup)
        (root / "src" / "deploy.key").write_text("synthetic\n", encoding="utf-8")
        _git(root, "add", ".")
        _git(root, "commit", "-qm", "denied path")

        with self.assertRaisesRegex(ApprovalRejected, "scope check"):
            build_proposal(root, "policy.json", base, "HEAD")

    def test_policy_path_cannot_escape_repository(self) -> None:
        temporary, root, base, head = _repository()
        self.addCleanup(temporary.cleanup)

        with self.assertRaisesRegex(ApprovalError, "stays inside"):
            build_proposal(root, "../policy.json", base, head)

    def test_git_revision_cannot_start_with_an_option(self) -> None:
        temporary, root, _, head = _repository()
        self.addCleanup(temporary.cleanup)

        with self.assertRaisesRegex(ApprovalError, "safe Git revision"):
            build_proposal(
                root,
                "policy.json",
                "--output=/tmp/result",
                head,
            )

    def test_unknown_proposal_field_is_rejected(self) -> None:
        temporary, root, base, head = _repository()
        self.addCleanup(temporary.cleanup)
        proposal = build_proposal(root, "policy.json", base, head)
        proposal["unexpected"] = True
        proposal_path = root / "proposal.json"
        proposal_path.write_text(serialize_proposal(proposal), encoding="utf-8")

        with self.assertRaisesRegex(ApprovalError, "fields"):
            load_proposal(proposal_path)


class ApprovalWorkflowTests(unittest.TestCase):
    def test_workflow_has_explicit_human_gate_and_read_only_token(self) -> None:
        workflow = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "human-approved-agent.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertIn("permissions:\n  actions: read\n  contents: read", workflow)
        self.assertIn("needs: validate-proposal", workflow)
        self.assertIn("name: agent-approval", workflow)
        self.assertEqual(workflow.count("persist-credentials: false"), 2)
        self.assertIn("check-environment", workflow)
        self.assertNotIn("write", workflow)
        self.assertNotIn("secrets.", workflow)

    def test_workflow_pins_official_actions_and_revalidates_artifact(self) -> None:
        workflow = (
            REPOSITORY_ROOT
            / ".github"
            / "workflows"
            / "human-approved-agent.yml"
        ).read_text(encoding="utf-8")

        expected_actions = {
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
        }
        for action in expected_actions:
            self.assertIn(action, workflow)
        self.assertIn("agent-proposal-${{ github.run_id }}", workflow)
        self.assertIn("agent_scope_guard.approval verify", workflow)
        self.assertIn("AGENT_SCOPE_HEAD_REF: ${{ github.sha }}", workflow)

    def test_environment_snapshot_requires_reviewer_and_branch_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            snapshot_path = Path(temporary) / "environment.json"
            snapshot = {
                "name": "agent-approval",
                "protection_rules": [
                    {
                        "type": "required_reviewers",
                        "prevent_self_review": False,
                        "reviewers": [
                            {
                                "type": "User",
                                "reviewer": {"login": "reviewer"},
                            }
                        ],
                    }
                ],
                "deployment_branch_policy": {
                    "protected_branches": False,
                    "custom_branch_policies": True,
                },
            }
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

            self.assertEqual(
                validate_environment_snapshot(
                    snapshot_path,
                    "agent-approval",
                ),
                snapshot,
            )

            snapshot["protection_rules"][0]["reviewers"] = []
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            with self.assertRaisesRegex(ApprovalRejected, "reviewer"):
                validate_environment_snapshot(
                    snapshot_path,
                    "agent-approval",
                )

            snapshot["protection_rules"][0]["reviewers"] = [
                {"type": "User", "reviewer": {"login": "reviewer"}}
            ]
            snapshot["deployment_branch_policy"] = {
                "protected_branches": False,
                "custom_branch_policies": False,
            }
            snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
            with self.assertRaisesRegex(ApprovalRejected, "branch policies"):
                validate_environment_snapshot(
                    snapshot_path,
                    "agent-approval",
                )


if __name__ == "__main__":
    unittest.main()
