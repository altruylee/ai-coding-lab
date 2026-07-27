"""Deterministically verify the human-approval reference workflow."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_scope_guard.approval import (  # noqa: E402
    ApprovalRejected,
    build_proposal,
    serialize_proposal,
    verify_proposal,
)


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


def main() -> int:
    workflow = (
        REPOSITORY_ROOT
        / ".github"
        / "workflows"
        / "human-approved-agent.yml"
    ).read_text(encoding="utf-8")
    required_fragments = [
        "workflow_dispatch:",
        "permissions:\n  actions: read\n  contents: read",
        "needs: validate-proposal",
        "name: agent-approval",
        "persist-credentials: false",
        "check-environment",
        "agent_scope_guard.approval prepare",
        "agent_scope_guard.approval verify",
        "agent-proposal-${{ github.run_id }}",
    ]
    if any(fragment not in workflow for fragment in required_fragments):
        raise AssertionError("approval workflow is missing a required safety control")
    if "pull_request_target:" in workflow:
        raise AssertionError("unsafe pull_request_target trigger is present")
    if "write" in workflow or "secrets." in workflow:
        raise AssertionError("reference workflow grants mutation authority")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "approval@example.invalid")
        _git(root, "config", "user.name", "Approval Verifier")
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
        (root / "README.md").write_text("synthetic repository\n", encoding="utf-8")
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

        proposal = build_proposal(root, "policy.json", base, head)
        proposal_path = Path(temporary) / "agent-proposal.json"
        proposal_path.write_text(serialize_proposal(proposal), encoding="utf-8")
        verified = verify_proposal(
            proposal_path,
            root,
            "policy.json",
            base,
            head,
        )
        if verified != proposal:
            raise AssertionError("unchanged proposal did not verify")

        tampered = dict(proposal)
        tampered["head_sha"] = base
        proposal_path.write_text(serialize_proposal(tampered), encoding="utf-8")
        try:
            verify_proposal(
                proposal_path,
                root,
                "policy.json",
                base,
                head,
            )
        except ApprovalRejected:
            pass
        else:
            raise AssertionError("tampered proposal was accepted")

    print("human approval workflow scenarios passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
