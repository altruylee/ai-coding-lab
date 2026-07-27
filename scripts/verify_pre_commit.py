"""Run deterministic end-to-end checks for the pre-commit entry point."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run_hook(
    directory: Path,
    *filenames: str,
    policy: str = "policy.json",
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT)
    if existing_pythonpath:
        environment["PYTHONPATH"] += os.pathsep + existing_pythonpath
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_scope_guard.pre_commit",
            "--policy",
            policy,
            "--format",
            "json",
            *filenames,
        ],
        cwd=directory,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _write_policy(directory: Path, payload: dict[str, object]) -> None:
    Path(directory, "policy.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def _verify_allowed_paths() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        _write_policy(
            directory,
            {
                "allowed_paths": ["src/**", "tests/**"],
                "required_paths": ["tests/**"],
            },
        )
        result = _run_hook(directory, "src/app.py", "tests/test_app.py")
        payload = json.loads(result.stdout)
        if result.returncode != 0 or not payload.get("ok"):
            raise RuntimeError("allowed staged paths did not pass")


def _verify_denied_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        _write_policy(
            directory,
            {
                "allowed_paths": ["**"],
                "denied_paths": ["**/*.key"],
            },
        )
        result = _run_hook(directory, "deploy.key")
        payload = json.loads(result.stdout)
        codes = {item.get("code") for item in payload.get("violations", [])}
        if result.returncode != 1 or "denied_path" not in codes:
            raise RuntimeError("denied staged path was not rejected")


def _verify_required_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        _write_policy(
            directory,
            {
                "allowed_paths": ["src/**", "tests/**"],
                "required_paths": ["tests/**"],
            },
        )
        result = _run_hook(directory, "src/app.py")
        payload = json.loads(result.stdout)
        codes = {item.get("code") for item in payload.get("violations", [])}
        if result.returncode != 1 or "required_path_missing" not in codes:
            raise RuntimeError("missing required staged path was not rejected")


def _verify_escaping_policy() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        result = _run_hook(directory, "src/app.py", policy="../policy.json")
        if result.returncode != 2:
            raise RuntimeError("escaping policy path was not rejected")


def main() -> int:
    """Verify staged-path success, failure, and configuration behavior."""

    try:
        _verify_allowed_paths()
        _verify_denied_path()
        _verify_required_path()
        _verify_escaping_policy()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"pre-commit integration verification failed: {exc}", file=sys.stderr)
        return 1
    print("pre-commit integration scenarios passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
