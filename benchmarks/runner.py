"""Run synthetic coding-agent tasks in temporary workspaces."""

from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from agent_scope_guard.evidence import EvidenceError, resolve_repository_path


class BenchmarkError(ValueError):
    """Raised when a benchmark task is invalid."""


def _task_hash(task_dir: Path) -> str:
    digest = hashlib.sha256()
    entries: list[tuple[str, Path]] = []
    for path in task_dir.rglob("*"):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_symlink():
            raise BenchmarkError(f"task contains unsupported symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(task_dir).as_posix()
        entries.append((relative, path))

    # WindowsPath ordering is case-insensitive while PosixPath ordering is not.
    # Sort the portable relative strings so identical task bytes hash identically.
    for relative, path in sorted(entries, key=lambda entry: entry[0]):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_task(task_dir: Path) -> dict[str, Any]:
    task_path = task_dir / "task.json"
    try:
        task = json.loads(task_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BenchmarkError(f"cannot read task.json: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise BenchmarkError(
            f"invalid task.json at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(task, dict):
        raise BenchmarkError("task.json must contain a JSON object")

    allowed = {
        "id",
        "title",
        "starter_dir",
        "reference_dir",
        "candidate_paths",
        "checks",
        "expected",
    }
    unknown = set(task) - allowed
    if unknown:
        raise BenchmarkError(f"unknown task field(s): {', '.join(sorted(unknown))}")

    for field in ("id", "title", "starter_dir", "reference_dir"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise BenchmarkError(f"{field} must be a non-empty string")

    candidate_paths = task.get("candidate_paths")
    if (
        not isinstance(candidate_paths, list)
        or not candidate_paths
        or not all(
            isinstance(pattern, str)
            and pattern
            and not pattern.startswith(("/", "\\"))
            and ".." not in pattern.replace("\\", "/").split("/")
            for pattern in candidate_paths
        )
    ):
        raise BenchmarkError(
            "candidate_paths must contain safe repository-relative patterns"
        )

    checks = task.get("checks")
    if not isinstance(checks, list) or not checks:
        raise BenchmarkError("checks must contain at least one command")
    names: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise BenchmarkError(f"checks[{index}] must be a JSON object")
        name = check.get("name")
        command = check.get("command")
        timeout = check.get("timeout_seconds", 300)
        if not isinstance(name, str) or not name:
            raise BenchmarkError(f"checks[{index}].name must be a non-empty string")
        if name in names:
            raise BenchmarkError(f"duplicate check name: {name}")
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
        ):
            raise BenchmarkError(
                f"checks[{index}].command must be a non-empty string array"
            )
        if not isinstance(timeout, int) or not 1 <= timeout <= 600:
            raise BenchmarkError(
                f"checks[{index}].timeout_seconds must be between 1 and 600"
            )
        names.add(name)

    expected = task.get("expected")
    if (
        not isinstance(expected, dict)
        or expected.get("starter") not in {"pass", "fail"}
        or expected.get("reference") not in {"pass", "fail"}
    ):
        raise BenchmarkError(
            "expected must declare starter and reference as pass or fail"
        )
    return task


def _task_child(task_dir: Path, value: str, label: str) -> Path:
    candidate = (task_dir / value).resolve()
    try:
        candidate.relative_to(task_dir.resolve())
    except ValueError as exc:
        raise BenchmarkError(f"{label} is outside the task directory") from exc
    if not candidate.is_dir():
        raise BenchmarkError(f"{label} is not a directory: {value}")
    return candidate


def _run_checks(
    checks: list[dict[str, Any]],
    workspace: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in checks:
        try:
            process = subprocess.run(
                check["command"],
                cwd=workspace,
                check=False,
                capture_output=True,
                timeout=check.get("timeout_seconds", 300),
            )
            exit_code = process.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            exit_code = 124
            timed_out = True
        except OSError:
            exit_code = 127
            timed_out = False
        results.append(
            {
                "name": check["name"],
                "command": list(check["command"]),
                "exit_code": exit_code,
                "timed_out": timed_out,
                "passed": exit_code == 0 and not timed_out,
            }
        )
    return results


def _run_variant(
    task_dir: Path,
    task: dict[str, Any],
    variant: str,
) -> dict[str, Any]:
    starter = _task_child(task_dir, task["starter_dir"], "starter_dir")
    reference = _task_child(task_dir, task["reference_dir"], "reference_dir")

    with tempfile.TemporaryDirectory(prefix=f"{task['id']}-{variant}-") as directory:
        workspace = Path(directory) / "workspace"
        ignored = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
        shutil.copytree(starter, workspace, ignore=ignored)
        if variant == "reference":
            shutil.copytree(
                reference,
                workspace,
                dirs_exist_ok=True,
                ignore=ignored,
            )
        checks = _run_checks(task["checks"], workspace)

    observed = "pass" if all(check["passed"] for check in checks) else "fail"
    expected = task["expected"][variant]
    return {
        "expected": expected,
        "observed": observed,
        "matches_expected": observed == expected,
        "checks": checks,
    }


def _candidate_files(candidate_dir: Path) -> list[str]:
    _task_hash(candidate_dir)
    return sorted(
        path.relative_to(candidate_dir).as_posix()
        for path in candidate_dir.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


def run_candidate(
    task_dir: str | Path,
    candidate_dir: str | Path,
) -> dict[str, Any]:
    """Run a candidate overlay without exposing the reference implementation."""

    directory = Path(task_dir).resolve()
    candidate = Path(candidate_dir).resolve()
    _task_hash(directory)
    task = _load_task(directory)
    starter = _task_child(directory, task["starter_dir"], "starter_dir")
    candidate_files = _candidate_files(candidate)
    if not candidate_files:
        raise BenchmarkError("candidate_dir must contain at least one file")

    patterns = [
        pattern.replace("\\", "/") for pattern in task["candidate_paths"]
    ]
    disallowed = [
        path
        for path in candidate_files
        if not any(fnmatchcase(path, pattern) for pattern in patterns)
    ]
    if disallowed:
        raise BenchmarkError(
            "candidate contains disallowed path(s): "
            + ", ".join(disallowed)
        )

    with tempfile.TemporaryDirectory(
        prefix=f"{task['id']}-candidate-"
    ) as directory_name:
        workspace = Path(directory_name) / "workspace"
        ignored = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
        shutil.copytree(starter, workspace, ignore=ignored)
        shutil.copytree(
            candidate,
            workspace,
            dirs_exist_ok=True,
            ignore=ignored,
        )
        checks = _run_checks(task["checks"], workspace)

    observed = "pass" if all(check["passed"] for check in checks) else "fail"
    return {
        "observed": observed,
        "solved": observed == "pass",
        "candidate_paths": candidate_files,
        "checks": checks,
    }


def run_benchmark(task_dir: str | Path) -> dict[str, Any]:
    """Run starter and reference variants for a benchmark task."""

    directory = Path(task_dir).resolve()
    task_sha256 = _task_hash(directory)
    task = _load_task(directory)
    starter = _run_variant(directory, task, "starter")
    reference = _run_variant(directory, task, "reference")
    valid = starter["matches_expected"] and reference["matches_expected"]
    return {
        "schema_version": 1,
        "task_id": task["id"],
        "title": task["title"],
        "task_sha256": task_sha256,
        "starter": starter,
        "reference": reference,
        "summary": {
            "benchmark_valid": valid,
            "starter_matches": starter["matches_expected"],
            "reference_matches": reference["matches_expected"],
        },
    }


def serialize_result(result: dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="task directory")
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
        task_dir = resolve_repository_path(args.repo_root, args.task, "task")
        output = resolve_repository_path(args.repo_root, args.output, "output")
        result = run_benchmark(task_dir)
        rendered = serialize_result(result)
        if args.write:
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"wrote benchmark result to {output}")
        else:
            if output.read_text(encoding="utf-8") != rendered:
                print("benchmark result does not match a fresh run")
                return 1
            print("benchmark result matches a fresh run")
        return 0 if result["summary"]["benchmark_valid"] else 1
    except (BenchmarkError, EvidenceError, OSError) as exc:
        print(f"benchmark error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
