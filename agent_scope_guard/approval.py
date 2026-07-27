"""Create and verify immutable inputs for a human-approved agent job."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Mapping, Sequence

from .policy import PolicyError, evaluate_paths, load_policy, violations_as_dicts


SCHEMA_VERSION = 1
MAX_CHANGED_PATHS = 10_000
_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@{}~^+-]{0,255}$")
_PROPOSAL_KEYS = frozenset(
    {
        "schema_version",
        "policy_path",
        "base_ref",
        "base_sha",
        "head_ref",
        "head_sha",
        "changed_paths",
        "scope",
        "proposal_sha256",
    }
)


class ApprovalError(ValueError):
    """Raised when approval inputs or proposal integrity are invalid."""


class ApprovalRejected(ApprovalError):
    """Raised when a safe execution must not continue."""


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validate_ref(value: str, label: str) -> str:
    ref = value.strip()
    if not _REF_PATTERN.fullmatch(ref) or "..." in ref:
        raise ApprovalError(f"{label} is not a safe Git revision")
    return ref


def _repository_file(
    repo_root: Path,
    value: str,
    label: str,
) -> tuple[Path, str]:
    normalized = value.strip().replace("\\", "/")
    pure_path = PurePosixPath(normalized)
    if (
        not normalized
        or pure_path.is_absolute()
        or ".." in pure_path.parts
    ):
        raise ApprovalError(
            f"{label} must be a repository-relative path that stays inside the repository"
        )
    resolved = (repo_root / Path(*pure_path.parts)).resolve()
    if not resolved.is_relative_to(repo_root):
        raise ApprovalError(f"{label} resolves outside the repository")
    return resolved, pure_path.as_posix()


def _run_git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raw_detail = getattr(exc, "stderr", b"") or str(exc).encode()
        detail = raw_detail.decode("utf-8", errors="replace").strip()
        raise ApprovalError(f"git command failed: {detail[:1000]}") from exc
    return completed.stdout


def _resolve_commit(repo_root: Path, ref: str) -> str:
    output = _run_git(repo_root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    sha = output.decode("ascii", errors="strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
        raise ApprovalError(f"Git returned an invalid commit ID for {ref}")
    return sha


def _changed_paths(repo_root: Path, base_ref: str, head_ref: str) -> list[str]:
    output = _run_git(
        repo_root,
        [
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            "--diff-filter=ACMR",
            "--relative",
            "-z",
            f"{base_ref}...{head_ref}",
        ],
    )
    raw_paths = output.split(b"\0")
    if raw_paths and raw_paths[-1] == b"":
        raw_paths.pop()
    if len(raw_paths) > MAX_CHANGED_PATHS:
        raise ApprovalError(
            f"Git diff exceeds the {MAX_CHANGED_PATHS} path limit"
        )

    changed_paths: list[str] = []
    for raw_path in raw_paths:
        try:
            path = raw_path.decode("utf-8", errors="strict").replace("\\", "/")
        except UnicodeDecodeError as exc:
            raise ApprovalError("Git path is not valid UTF-8") from exc
        if not path or any(ord(character) < 32 or ord(character) == 127 for character in path):
            raise ApprovalError("Git path contains a control character")
        changed_paths.append(path)
    return changed_paths


def build_proposal(
    repo_root: str | Path,
    policy_path: str,
    base_ref: str,
    head_ref: str,
) -> dict[str, object]:
    """Build a deterministic, scope-checked approval proposal."""

    root = Path(repo_root).resolve()
    if not root.is_dir():
        raise ApprovalError(f"repository root is not a directory: {root}")
    policy_file, normalized_policy = _repository_file(
        root,
        policy_path,
        "policy",
    )
    safe_base = _validate_ref(base_ref, "base_ref")
    safe_head = _validate_ref(head_ref, "head_ref")
    base_sha = _resolve_commit(root, safe_base)
    head_sha = _resolve_commit(root, safe_head)
    changed_paths = _changed_paths(root, base_sha, head_sha)
    try:
        violations = evaluate_paths(load_policy(policy_file), changed_paths)
    except PolicyError as exc:
        raise ApprovalError(str(exc)) from exc
    if violations:
        codes = ", ".join(violation.code for violation in violations)
        raise ApprovalRejected(f"scope check rejected the proposal: {codes}")

    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "policy_path": normalized_policy,
        "base_ref": safe_base,
        "base_sha": base_sha,
        "head_ref": safe_head,
        "head_sha": head_sha,
        "changed_paths": changed_paths,
        "scope": {
            "ok": True,
            "violations": violations_as_dicts(violations),
        },
    }
    return {**payload, "proposal_sha256": _digest(payload)}


def serialize_proposal(proposal: Mapping[str, object]) -> str:
    """Serialize a proposal for a workflow artifact."""

    return json.dumps(
        proposal,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def load_proposal(path: str | Path) -> dict[str, object]:
    """Load and structurally validate a proposal artifact."""

    proposal_path = Path(path)
    try:
        data = json.loads(proposal_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ApprovalError(f"cannot read proposal {proposal_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ApprovalError(
            f"invalid proposal JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(data, dict):
        raise ApprovalError("proposal root must be a JSON object")
    if set(data) != _PROPOSAL_KEYS:
        raise ApprovalError("proposal fields do not match the supported schema")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ApprovalError("unsupported proposal schema version")
    digest = data.get("proposal_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ApprovalError("proposal_sha256 must be a lowercase SHA-256 digest")
    unsigned = {key: value for key, value in data.items() if key != "proposal_sha256"}
    if _digest(unsigned) != digest:
        raise ApprovalRejected("proposal digest does not match its content")
    return data


def verify_proposal(
    proposal_path: str | Path,
    repo_root: str | Path,
    policy_path: str,
    base_ref: str,
    head_ref: str,
) -> dict[str, object]:
    """Verify artifact integrity and reject a changed Git target."""

    recorded = load_proposal(proposal_path)
    fresh = build_proposal(repo_root, policy_path, base_ref, head_ref)
    if recorded != fresh:
        raise ApprovalRejected(
            "proposal no longer matches the policy, refs, or changed paths"
        )
    return recorded


def validate_environment_snapshot(
    path: str | Path,
    expected_name: str,
) -> dict[str, object]:
    """Fail closed unless a GitHub environment has a required reviewer."""

    snapshot_path = Path(path)
    try:
        data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ApprovalError(
            f"cannot read environment snapshot {snapshot_path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ApprovalError(
            f"invalid environment JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(data, dict) or data.get("name") != expected_name:
        raise ApprovalRejected("approval environment name does not match")

    rules = data.get("protection_rules")
    if not isinstance(rules, list):
        raise ApprovalRejected("approval environment has no protection rules")
    reviewer_rules = [
        rule
        for rule in rules
        if isinstance(rule, dict) and rule.get("type") == "required_reviewers"
    ]
    if len(reviewer_rules) != 1:
        raise ApprovalRejected(
            "approval environment must have one required-reviewers rule"
        )
    reviewers = reviewer_rules[0].get("reviewers")
    if not isinstance(reviewers, list) or not reviewers:
        raise ApprovalRejected(
            "approval environment must name at least one reviewer"
        )

    branch_policy = data.get("deployment_branch_policy")
    if (
        not isinstance(branch_policy, dict)
        or branch_policy.get("protected_branches") is not False
        or branch_policy.get("custom_branch_policies") is not True
    ):
        raise ApprovalRejected(
            "approval environment must use custom deployment branch policies"
        )
    return data


def _write_summary(path: str | Path, proposal: Mapping[str, object]) -> None:
    summary = {
        "policy_path": proposal["policy_path"],
        "base_sha": proposal["base_sha"],
        "head_sha": proposal["head_sha"],
        "changed_paths": proposal["changed_paths"],
        "proposal_sha256": proposal["proposal_sha256"],
    }
    rendered = html.escape(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
    )
    Path(path).write_text(
        "# Agent proposal awaiting human approval\n\n"
        "Review the immutable proposal artifact and the following scope summary.\n\n"
        f"<pre>{rendered}</pre>\n",
        encoding="utf-8",
    )


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_scope_guard.approval",
        description="Prepare or verify a human-approval proposal artifact.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare")
    _common_arguments(prepare)
    prepare.add_argument("--output", required=True)
    prepare.add_argument("--summary")

    verify = commands.add_parser("verify")
    _common_arguments(verify)
    verify.add_argument("--proposal", required=True)

    environment = commands.add_parser("check-environment")
    environment.add_argument("--input", required=True)
    environment.add_argument("--name", default="agent-approval")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the approval proposal command."""

    args = _build_parser().parse_args(argv)
    try:
        if args.command == "check-environment":
            snapshot = validate_environment_snapshot(args.input, args.name)
            rule = next(
                item
                for item in snapshot["protection_rules"]
                if isinstance(item, dict)
                and item.get("type") == "required_reviewers"
            )
            print(
                "approval environment verified: "
                f"{len(rule['reviewers'])} reviewer(s)"
            )
            return 0

        if args.command == "prepare":
            proposal = build_proposal(
                args.repo_root,
                args.policy,
                args.base_ref,
                args.head_ref,
            )
            Path(args.output).write_text(
                serialize_proposal(proposal),
                encoding="utf-8",
            )
            if args.summary:
                _write_summary(args.summary, proposal)
            print(
                "proposal ready: "
                f"{len(proposal['changed_paths'])} path(s), "
                f"sha256={proposal['proposal_sha256']}"
            )
            return 0

        proposal = verify_proposal(
            args.proposal,
            args.repo_root,
            args.policy,
            args.base_ref,
            args.head_ref,
        )
        print(f"approved proposal verified: sha256={proposal['proposal_sha256']}")
        return 0
    except ApprovalRejected as exc:
        print(f"approval rejected: {exc}", file=sys.stderr)
        return 1
    except (ApprovalError, OSError) as exc:
        print(f"approval configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
