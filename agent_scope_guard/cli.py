"""Command-line interface for Agent Scope Guard."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Sequence

from .policy import PolicyError, evaluate_paths, load_policy, violations_as_dicts


def _changed_paths_from_git(base_ref: str, head_ref: str) -> list[str]:
    command = [
        "git",
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        "--relative",
        f"{base_ref}...{head_ref}",
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        raise PolicyError(f"git diff failed: {detail.strip()}") from exc
    return [line for line in result.stdout.splitlines() if line.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-scope-guard",
        description="Check whether changed files stay inside an AI coding policy.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="evaluate changed files")
    check.add_argument("--policy", required=True, help="path to a JSON policy")
    check.add_argument(
        "--changed-path",
        action="append",
        default=[],
        help="changed repository path; may be supplied more than once",
    )
    check.add_argument("--base-ref", help="Git base ref used when no paths are given")
    check.add_argument("--head-ref", default="HEAD", help="Git head ref")
    check.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    return parser


def _print_result(
    changed_paths: Sequence[str],
    violations: Sequence[object],
    output_format: str,
) -> None:
    if output_format == "json":
        payload = {
            "ok": not violations,
            "changed_paths": list(changed_paths),
            "violations": violations_as_dicts(violations),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not violations:
        print(f"scope check passed for {len(changed_paths)} changed path(s)")
        return

    print(f"scope check failed with {len(violations)} violation(s)")
    for violation in violations:
        print(f"- [{violation.code}] {violation.message}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        policy = load_policy(args.policy)
        changed_paths = list(args.changed_path)
        if not changed_paths:
            if not args.base_ref:
                parser.error("--base-ref is required when --changed-path is omitted")
            changed_paths = _changed_paths_from_git(args.base_ref, args.head_ref)
        violations = evaluate_paths(policy, changed_paths)
    except PolicyError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    _print_result(changed_paths, violations, args.format)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
