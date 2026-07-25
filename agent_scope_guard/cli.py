"""Command-line interface for Agent Scope Guard."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .evidence import (
    EvidenceError,
    build_evidence_bundle,
    resolve_repository_path,
    serialize_evidence,
    verify_evidence_bundle,
    write_evidence_bundle,
)
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

    evidence = subparsers.add_parser(
        "evidence",
        help="run declared checks and create a task evidence bundle",
    )
    evidence.add_argument("--manifest", required=True, help="evidence manifest")
    evidence.add_argument("--output", required=True, help="bundle output path")
    evidence.add_argument(
        "--repo-root",
        default=".",
        help="repository root used for paths and check commands",
    )
    evidence.add_argument(
        "--verify",
        action="store_true",
        help="compare a fresh run with the existing output instead of writing",
    )

    verify = subparsers.add_parser(
        "verify-evidence",
        help="verify bundle and referenced input integrity without running checks",
    )
    verify.add_argument("--bundle", required=True, help="evidence bundle path")
    verify.add_argument("--repo-root", default=".", help="repository root")
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

    if args.command == "evidence":
        try:
            bundle = build_evidence_bundle(args.manifest, args.repo_root)
            rendered = serialize_evidence(bundle)
            output = resolve_repository_path(
                args.repo_root,
                args.output,
                "output",
            )
            if args.verify:
                committed = output.read_text(encoding="utf-8")
                if committed != rendered:
                    print(
                        "evidence bundle does not match a fresh run",
                        file=sys.stderr,
                    )
                    return 1
                print("evidence bundle matches a fresh run")
            else:
                write_evidence_bundle(output, bundle)
                print(f"wrote evidence bundle to {output}")
            return 0 if bundle["summary"]["ok"] else 1
        except (EvidenceError, PolicyError, OSError) as exc:
            print(f"evidence error: {exc}", file=sys.stderr)
            return 2

    if args.command == "verify-evidence":
        try:
            errors = verify_evidence_bundle(args.bundle, args.repo_root)
        except EvidenceError as exc:
            print(f"evidence error: {exc}", file=sys.stderr)
            return 2
        if errors:
            print("evidence verification failed", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1
        print("evidence integrity verified")
        return 0

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
