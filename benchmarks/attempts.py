"""Validate recorded coding-agent attempts in isolated workspaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping

from agent_scope_guard.evidence import EvidenceError, resolve_repository_path
from benchmarks.runner import (
    BenchmarkError,
    _task_hash,
    run_candidate,
)


class AttemptError(ValueError):
    """Raised when an attempt manifest is invalid."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AttemptError(f"cannot read attempt manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AttemptError(
            f"invalid attempt JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise AttemptError("attempt manifest must contain a JSON object")
    return value


def _require_fields(
    value: object,
    label: str,
    allowed: set[str],
    required: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AttemptError(f"{label} must be a JSON object")
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        raise AttemptError(
            f"unknown {label} field(s): {', '.join(sorted(unknown))}"
        )
    if missing:
        raise AttemptError(
            f"missing {label} field(s): {', '.join(sorted(missing))}"
        )
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AttemptError(f"{label} must be null or a non-empty string")
    return value


def _optional_non_negative_integer(
    value: object,
    label: str,
) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AttemptError(f"{label} must be null or a non-negative integer")
    return value


def _parse_attempt(path: Path) -> dict[str, Any]:
    attempt = _require_fields(
        _load_object(path),
        "attempt",
        {
            "schema_version",
            "attempt_id",
            "task",
            "candidate_dir",
            "provenance",
            "execution",
            "usage",
        },
        {
            "schema_version",
            "attempt_id",
            "task",
            "candidate_dir",
            "provenance",
            "execution",
            "usage",
        },
    )
    if (
        isinstance(attempt["schema_version"], bool)
        or attempt["schema_version"] != 1
    ):
        raise AttemptError("schema_version must be 1")
    for field in ("attempt_id", "task", "candidate_dir"):
        if (
            not isinstance(attempt[field], str)
            or not attempt[field].strip()
        ):
            raise AttemptError(f"{field} must be a non-empty string")

    provenance = _require_fields(
        attempt["provenance"],
        "provenance",
        {
            "kind",
            "agent_name",
            "agent_version",
            "model",
            "reference_access",
        },
        {
            "kind",
            "agent_name",
            "agent_version",
            "model",
            "reference_access",
        },
    )
    if provenance["kind"] not in {"agent", "human", "fixture"}:
        raise AttemptError("provenance.kind must be agent, human, or fixture")
    for field in ("agent_name", "agent_version", "model"):
        _optional_text(provenance[field], f"provenance.{field}")
    if not isinstance(provenance["reference_access"], bool):
        raise AttemptError("provenance.reference_access must be boolean")
    if provenance["kind"] == "agent":
        if provenance["agent_name"] is None or provenance["model"] is None:
            raise AttemptError(
                "agent attempts must disclose agent_name and model"
            )

    execution = _require_fields(
        attempt["execution"],
        "execution",
        {
            "permissions",
            "network_access",
            "elapsed_ms",
            "human_interventions",
        },
        {
            "permissions",
            "network_access",
            "elapsed_ms",
            "human_interventions",
        },
    )
    permissions = execution["permissions"]
    if (
        not isinstance(permissions, list)
        or not permissions
        or not all(
            isinstance(permission, str) and permission.strip()
            for permission in permissions
        )
        or len(set(permissions)) != len(permissions)
    ):
        raise AttemptError(
            "execution.permissions must contain unique non-empty strings"
        )
    if execution["network_access"] not in {
        "disabled",
        "restricted",
        "enabled",
        "unknown",
    }:
        raise AttemptError(
            "execution.network_access must be disabled, restricted, "
            "enabled, or unknown"
        )
    _optional_non_negative_integer(
        execution["elapsed_ms"],
        "execution.elapsed_ms",
    )
    interventions = _optional_non_negative_integer(
        execution["human_interventions"],
        "execution.human_interventions",
    )
    if interventions is None:
        raise AttemptError("execution.human_interventions must be recorded")

    usage = _require_fields(
        attempt["usage"],
        "usage",
        {"input_tokens", "output_tokens", "cost_usd"},
        {"input_tokens", "output_tokens", "cost_usd"},
    )
    _optional_non_negative_integer(usage["input_tokens"], "usage.input_tokens")
    _optional_non_negative_integer(
        usage["output_tokens"],
        "usage.output_tokens",
    )
    cost = usage["cost_usd"]
    if (
        cost is not None
        and (
            isinstance(cost, bool)
            or not isinstance(cost, (int, float))
            or not math.isfinite(cost)
            or cost < 0
        )
    ):
        raise AttemptError("usage.cost_usd must be null or non-negative")
    return attempt


def _resolve_candidate(manifest: Path, value: str) -> Path:
    attempt_root = manifest.parent.resolve()
    candidate = (attempt_root / value).resolve()
    try:
        candidate.relative_to(attempt_root)
    except ValueError as exc:
        raise AttemptError(
            "candidate_dir is outside the attempt directory"
        ) from exc
    if not candidate.is_dir():
        raise AttemptError(f"candidate_dir is not a directory: {value}")
    return candidate


def build_attempt_result(
    attempt_path: str | Path,
    repository_root: str | Path,
) -> dict[str, Any]:
    """Run an attempt and return deterministic provenance and check results."""

    root = Path(repository_root).resolve()
    manifest = resolve_repository_path(root, attempt_path, "attempt")
    attempt = _parse_attempt(manifest)
    task = resolve_repository_path(root, attempt["task"], "task")
    candidate = _resolve_candidate(manifest, attempt["candidate_dir"])
    candidate_result = run_candidate(task, candidate)

    provenance = attempt["provenance"]
    execution = attempt["execution"]
    usage = attempt["usage"]
    eligible = (
        candidate_result["solved"]
        and provenance["kind"] == "agent"
        and not provenance["reference_access"]
        and execution["elapsed_ms"] is not None
        and execution["network_access"] != "unknown"
    )
    usage_complete = all(value is not None for value in usage.values())

    return {
        "schema_version": 1,
        "attempt_id": attempt["attempt_id"],
        "attempt_manifest": {
            "path": manifest.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        },
        "task": {
            "path": task.relative_to(root).as_posix(),
            "sha256": _task_hash(task),
        },
        "candidate": {
            "path": candidate.relative_to(root).as_posix(),
            "sha256": _task_hash(candidate),
            "changed_paths": candidate_result["candidate_paths"],
        },
        "provenance": provenance,
        "execution": execution,
        "usage": usage,
        "checks": candidate_result["checks"],
        "summary": {
            "solved": candidate_result["solved"],
            "observed": candidate_result["observed"],
            "scoreboard_eligible": eligible,
            "usage_complete": usage_complete,
        },
    }


def serialize_attempt_result(result: Mapping[str, Any]) -> str:
    """Serialize an attempt result with stable formatting."""

    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, help="attempt manifest")
    parser.add_argument("--output", required=True, help="result JSON path")
    parser.add_argument("--repo-root", default=".", help="repository root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the result")
    mode.add_argument(
        "--verify",
        action="store_true",
        help="compare a fresh run with the committed result",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        root = Path(args.repo_root).resolve()
        attempt = resolve_repository_path(root, args.attempt, "attempt")
        output = resolve_repository_path(root, args.output, "output")
        result = build_attempt_result(attempt, root)
        rendered = serialize_attempt_result(result)
        if args.write:
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"wrote attempt result to {output}")
        elif output.read_text(encoding="utf-8") != rendered:
            print("attempt result does not match a fresh run")
            return 1
        else:
            print("attempt result matches a fresh run")
        return 0 if result["summary"]["solved"] else 1
    except (AttemptError, BenchmarkError, EvidenceError, OSError) as exc:
        print(f"attempt error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
