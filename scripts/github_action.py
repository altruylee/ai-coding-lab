"""GitHub Action entry point for Agent Scope Guard."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path, PurePosixPath
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_scope_guard.cli import main as scope_guard_main


class ActionInputError(ValueError):
    """Raised when required composite-action inputs are missing or invalid."""


def build_cli_arguments(environment: Mapping[str, str]) -> list[str]:
    """Translate the composite action environment into CLI arguments."""

    policy = environment.get("AGENT_SCOPE_POLICY", "").strip()
    base_ref = environment.get("AGENT_SCOPE_BASE_REF", "").strip()
    head_ref = environment.get("AGENT_SCOPE_HEAD_REF", "HEAD").strip() or "HEAD"
    output_format = (
        environment.get("AGENT_SCOPE_OUTPUT_FORMAT", "text").strip() or "text"
    )

    if not policy:
        raise ActionInputError("policy input must not be empty")
    normalized_policy = policy.replace("\\", "/")
    if Path(policy).is_absolute() or ".." in PurePosixPath(normalized_policy).parts:
        raise ActionInputError("policy input must stay inside the repository")
    if not base_ref:
        raise ActionInputError("base_ref input must not be empty")
    if output_format not in {"text", "json"}:
        raise ActionInputError("output_format must be text or json")

    return [
        "check",
        "--policy",
        policy,
        "--base-ref",
        base_ref,
        "--head-ref",
        head_ref,
        "--format",
        output_format,
    ]


def main() -> int:
    """Run the scope check using GitHub Action inputs."""

    try:
        arguments = build_cli_arguments(os.environ)
    except ActionInputError as exc:
        print(f"action input error: {exc}", file=sys.stderr)
        return 2
    return scope_guard_main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
