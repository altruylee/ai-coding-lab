"""Create and verify privacy-conscious task evidence bundles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

from . import __version__
from .policy import evaluate_paths, load_policy, normalize_changed_path


class EvidenceError(ValueError):
    """Raised when an evidence manifest or bundle is invalid."""


@dataclass(frozen=True, slots=True)
class CheckSpec:
    """A verification command declared by an evidence manifest."""

    name: str
    command: tuple[str, ...]
    timeout_seconds: int


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _ensure_inside(repository_root: Path, path: Path, label: str) -> Path:
    root = repository_root.resolve()
    resolved = path.resolve()
    try:
        common = Path(os.path.commonpath((root, resolved)))
    except ValueError as exc:
        raise EvidenceError(f"{label} is outside the repository") from exc
    if common != root:
        raise EvidenceError(f"{label} is outside the repository")
    return resolved


def resolve_repository_path(
    repository_root: str | Path,
    path: str | Path,
    label: str,
) -> Path:
    """Resolve a relative or absolute path and require repository containment."""

    root = Path(repository_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return _ensure_inside(root, candidate, label)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvidenceError(f"cannot read {label} {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceError(
            f"invalid JSON in {label} at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"{label} must contain a JSON object")
    return value


def _parse_checks(value: object) -> tuple[CheckSpec, ...]:
    if not isinstance(value, list) or not value:
        raise EvidenceError("checks must contain at least one command")

    checks: list[CheckSpec] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EvidenceError(f"checks[{index}] must be a JSON object")
        name = item.get("name")
        command = item.get("command")
        timeout = item.get("timeout_seconds", 300)
        if not isinstance(name, str) or not name.strip():
            raise EvidenceError(f"checks[{index}].name must be a non-empty string")
        if name in names:
            raise EvidenceError(f"duplicate check name: {name}")
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
        ):
            raise EvidenceError(
                f"checks[{index}].command must be a non-empty string array"
            )
        if not isinstance(timeout, int) or not 1 <= timeout <= 600:
            raise EvidenceError(
                f"checks[{index}].timeout_seconds must be between 1 and 600"
            )
        names.add(name)
        checks.append(
            CheckSpec(
                name=name,
                command=tuple(command),
                timeout_seconds=timeout,
            )
        )
    return tuple(checks)


def _parse_manifest(
    manifest_path: Path,
    repository_root: Path,
) -> tuple[dict[str, Any], Path, tuple[str, ...], tuple[CheckSpec, ...]]:
    manifest = _load_json_object(manifest_path, "manifest")
    allowed_fields = {"task_id", "policy_path", "changed_paths", "checks"}
    unknown = set(manifest) - allowed_fields
    if unknown:
        raise EvidenceError(
            f"unknown manifest field(s): {', '.join(sorted(unknown))}"
        )

    task_id = manifest.get("task_id")
    policy_value = manifest.get("policy_path")
    changed_value = manifest.get("changed_paths")
    if not isinstance(task_id, str) or not task_id.strip():
        raise EvidenceError("task_id must be a non-empty string")
    if not isinstance(policy_value, str) or not policy_value.strip():
        raise EvidenceError("policy_path must be a non-empty string")
    if not isinstance(changed_value, list) or not changed_value:
        raise EvidenceError("changed_paths must contain at least one path")
    if not all(isinstance(path, str) for path in changed_value):
        raise EvidenceError("changed_paths must contain only strings")

    policy_path = _ensure_inside(
        repository_root,
        repository_root / policy_value,
        "policy_path",
    )
    changed_paths = tuple(normalize_changed_path(path) for path in changed_value)
    checks = _parse_checks(manifest.get("checks"))
    return manifest, policy_path, changed_paths, checks


def _to_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8", errors="replace")


def _normalize_output(value: bytes) -> bytes:
    return value.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _run_check(spec: CheckSpec, repository_root: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            list(spec.command),
            cwd=repository_root,
            check=False,
            capture_output=True,
            timeout=spec.timeout_seconds,
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = _to_bytes(exc.stdout)
        stderr = _to_bytes(exc.stderr)
        exit_code = 124
        timed_out = True
    except OSError as exc:
        stdout = b""
        stderr = str(exc).encode("utf-8", errors="replace")
        exit_code = 127
        timed_out = False

    return {
        "name": spec.name,
        "command": list(spec.command),
        "timeout_seconds": spec.timeout_seconds,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "output_normalization": "crlf-to-lf",
        "stdout_sha256": _sha256_bytes(_normalize_output(stdout)),
        "stderr_sha256": _sha256_bytes(_normalize_output(stderr)),
        "passed": exit_code == 0 and not timed_out,
    }


def build_evidence_bundle(
    manifest_path: str | Path,
    repository_root: str | Path,
) -> dict[str, Any]:
    """Run declared checks and return a hashed evidence bundle."""

    root = Path(repository_root).resolve()
    manifest = resolve_repository_path(root, manifest_path, "manifest")
    manifest_data, policy_path, changed_paths, checks = _parse_manifest(
        manifest,
        root,
    )

    policy = load_policy(policy_path)
    violations = evaluate_paths(policy, changed_paths)
    check_results = [_run_check(check, root) for check in checks]
    scope_ok = not violations
    passed_checks = sum(1 for check in check_results if check["passed"])

    payload: dict[str, Any] = {
        "schema_version": 1,
        "tool": {
            "name": "agent-scope-guard",
            "version": __version__,
        },
        "task_id": manifest_data["task_id"],
        "manifest": {
            "path": manifest.relative_to(root).as_posix(),
            "sha256": _sha256_bytes(manifest.read_bytes()),
        },
        "policy": {
            "path": policy_path.relative_to(root).as_posix(),
            "sha256": _sha256_bytes(policy_path.read_bytes()),
        },
        "changed_paths": list(changed_paths),
        "scope": {
            "ok": scope_ok,
            "violations": [
                {
                    "code": violation.code,
                    "path": violation.path,
                    "pattern": violation.pattern,
                }
                for violation in violations
            ],
        },
        "checks": check_results,
        "summary": {
            "ok": scope_ok and passed_checks == len(check_results),
            "scope_ok": scope_ok,
            "checks": len(check_results),
            "checks_passed": passed_checks,
            "checks_failed": len(check_results) - passed_checks,
        },
    }
    payload["bundle_sha256"] = _sha256_bytes(_canonical_bytes(payload))
    return payload


def serialize_evidence(bundle: Mapping[str, Any]) -> str:
    """Serialize an evidence bundle for stable review."""

    return json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"


def write_evidence_bundle(path: str | Path, bundle: Mapping[str, Any]) -> None:
    """Write a UTF-8 evidence bundle with LF line endings."""

    Path(path).write_text(
        serialize_evidence(bundle),
        encoding="utf-8",
        newline="\n",
    )


def verify_evidence_bundle(
    bundle_path: str | Path,
    repository_root: str | Path,
) -> tuple[str, ...]:
    """Verify bundle integrity and referenced input hashes."""

    root = Path(repository_root).resolve()
    path = resolve_repository_path(root, bundle_path, "bundle")
    bundle = _load_json_object(path, "bundle")
    errors: list[str] = []

    recorded_hash = bundle.pop("bundle_sha256", None)
    expected_hash = _sha256_bytes(_canonical_bytes(bundle))
    if recorded_hash != expected_hash:
        errors.append("bundle_sha256 does not match bundle contents")

    for label in ("manifest", "policy"):
        reference = bundle.get(label)
        if not isinstance(reference, dict):
            errors.append(f"{label} reference is missing")
            continue
        relative = reference.get("path")
        recorded = reference.get("sha256")
        if not isinstance(relative, str) or not isinstance(recorded, str):
            errors.append(f"{label} reference is invalid")
            continue
        try:
            referenced_path = _ensure_inside(
                root,
                root / relative,
                f"{label} path",
            )
            actual = _sha256_bytes(referenced_path.read_bytes())
        except (EvidenceError, OSError) as exc:
            errors.append(f"cannot verify {label}: {exc}")
            continue
        if actual != recorded:
            errors.append(f"{label} sha256 does not match current file")

    return tuple(errors)
