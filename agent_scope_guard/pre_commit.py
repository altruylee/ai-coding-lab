"""pre-commit entry point for Agent Scope Guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Sequence

from .policy import PolicyError, evaluate_paths, load_policy, violations_as_dicts


class HookInputError(ValueError):
    """Raised when a pre-commit hook option is unsafe or invalid."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-scope-guard-pre-commit",
        description="Check pre-commit staged paths against an AI coding policy.",
    )
    parser.add_argument(
        "--policy",
        default=".agent-scope-guard.json",
        help="repository-relative JSON policy path",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="repository-relative staged paths supplied by pre-commit",
    )
    return parser


def _validate_policy_path(value: str) -> str:
    policy = value.strip()
    if not policy:
        raise HookInputError("policy path must not be empty")
    normalized = policy.replace("\\", "/")
    if Path(policy).is_absolute() or ".." in PurePosixPath(normalized).parts:
        raise HookInputError("policy path must stay inside the repository")
    return policy


def _print_result(
    filenames: Sequence[str],
    violations: Sequence[object],
    output_format: str,
) -> None:
    if output_format == "json":
        payload = {
            "ok": not violations,
            "changed_paths": list(filenames),
            "violations": violations_as_dicts(violations),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if not violations:
        print(f"scope check passed for {len(filenames)} staged path(s)")
        return

    print(f"scope check failed with {len(violations)} violation(s)")
    for violation in violations:
        print(f"- [{violation.code}] {violation.message}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the pre-commit hook."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        policy_path = _validate_policy_path(args.policy)
        violations = evaluate_paths(load_policy(policy_path), args.filenames)
    except (HookInputError, PolicyError) as exc:
        print(f"hook configuration error: {exc}", file=sys.stderr)
        return 2

    _print_result(args.filenames, violations, args.format)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
