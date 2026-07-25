"""Policy loading and scope evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


class PolicyError(ValueError):
    """Raised when a policy or changed path is invalid."""


@dataclass(frozen=True, slots=True)
class Policy:
    """Allowed, denied, and required path patterns."""

    allowed_paths: tuple[str, ...]
    denied_paths: tuple[str, ...] = ()
    required_paths: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ScopeViolation:
    """A single policy violation."""

    code: str
    path: str
    pattern: str | None
    message: str


_POLICY_KEYS = frozenset({"allowed_paths", "denied_paths", "required_paths"})


def _normalize_relative_text(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _validate_patterns(value: object, key: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise PolicyError(f"{key} must be a JSON array of path patterns")

    patterns: list[str] = []
    for index, pattern in enumerate(value):
        if not isinstance(pattern, str) or not pattern.strip():
            raise PolicyError(f"{key}[{index}] must be a non-empty string")
        normalized = _normalize_relative_text(pattern)
        if normalized.startswith("/") or ".." in PurePosixPath(normalized).parts:
            raise PolicyError(f"{key}[{index}] must stay inside the repository")
        patterns.append(normalized)
    return tuple(patterns)


def policy_from_mapping(data: Mapping[str, object]) -> Policy:
    """Build and validate a policy from a decoded JSON object."""

    unknown = set(data) - _POLICY_KEYS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise PolicyError(f"unknown policy field(s): {names}")

    allowed = _validate_patterns(data.get("allowed_paths"), "allowed_paths")
    if not allowed:
        raise PolicyError("allowed_paths must contain at least one pattern")

    return Policy(
        allowed_paths=allowed,
        denied_paths=_validate_patterns(data.get("denied_paths"), "denied_paths"),
        required_paths=_validate_patterns(
            data.get("required_paths"), "required_paths"
        ),
    )


def load_policy(path: str | Path) -> Policy:
    """Load a UTF-8 JSON policy from disk."""

    policy_path = Path(path)
    try:
        raw = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyError(f"cannot read policy {policy_path}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PolicyError(
            f"invalid JSON in {policy_path} at line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(data, dict):
        raise PolicyError("policy root must be a JSON object")
    return policy_from_mapping(data)


def normalize_changed_path(path: str) -> str:
    """Normalize a Git-style repository-relative path."""

    normalized = _normalize_relative_text(path)
    if not normalized:
        raise PolicyError("changed paths must not be empty")

    pure_path = PurePosixPath(normalized)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise PolicyError(f"changed path escapes the repository: {path}")
    return pure_path.as_posix()


def _matches(path: str, pattern: str) -> bool:
    if fnmatchcase(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatchcase(path, pattern[3:])
    return False


def evaluate_paths(
    policy: Policy, changed_paths: Iterable[str]
) -> tuple[ScopeViolation, ...]:
    """Evaluate changed paths and return every scope violation."""

    paths = tuple(dict.fromkeys(normalize_changed_path(path) for path in changed_paths))
    violations: list[ScopeViolation] = []

    for path in paths:
        denied = next(
            (pattern for pattern in policy.denied_paths if _matches(path, pattern)),
            None,
        )
        if denied is not None:
            violations.append(
                ScopeViolation(
                    code="denied_path",
                    path=path,
                    pattern=denied,
                    message=f"{path} matches denied pattern {denied}",
                )
            )
            continue

        if not any(_matches(path, pattern) for pattern in policy.allowed_paths):
            violations.append(
                ScopeViolation(
                    code="outside_allowed_scope",
                    path=path,
                    pattern=None,
                    message=f"{path} is outside every allowed path pattern",
                )
            )

    for pattern in policy.required_paths:
        if not any(_matches(path, pattern) for path in paths):
            violations.append(
                ScopeViolation(
                    code="required_path_missing",
                    path="",
                    pattern=pattern,
                    message=f"no changed path matches required pattern {pattern}",
                )
            )

    return tuple(violations)


def violations_as_dicts(
    violations: Sequence[ScopeViolation],
) -> list[dict[str, str | None]]:
    """Convert violations into JSON-serializable dictionaries."""

    return [
        {
            "code": violation.code,
            "path": violation.path,
            "pattern": violation.pattern,
            "message": violation.message,
        }
        for violation in violations
    ]
