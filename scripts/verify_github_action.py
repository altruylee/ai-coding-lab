"""Run deterministic end-to-end checks for the composite GitHub Action."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ACTION_ENTRYPOINT = REPOSITORY_ROOT / "scripts" / "github_action.py"
ACTION_VARIABLES = {
    "AGENT_SCOPE_POLICY",
    "AGENT_SCOPE_BASE_REF",
    "AGENT_SCOPE_HEAD_REF",
    "AGENT_SCOPE_OUTPUT_FORMAT",
}


def _run(command: list[str], directory: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=directory,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _git(directory: Path, *arguments: str) -> None:
    result = _run(["git", *arguments], directory)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")


def _initialize_repository(directory: Path, policy: dict[str, object]) -> None:
    _git(directory, "init", "--quiet")
    _git(directory, "config", "user.name", "Action Verifier")
    _git(directory, "config", "user.email", "action-verifier@example.invalid")
    Path(directory, "policy.json").write_text(
        json.dumps(policy),
        encoding="utf-8",
    )
    source = Path(directory, "src", "app.py")
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    _git(directory, "add", "policy.json", "src/app.py")
    _git(directory, "commit", "--quiet", "-m", "initial")


def _run_action(directory: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for name in ACTION_VARIABLES:
        environment.pop(name, None)
    environment.update(
        {
            "AGENT_SCOPE_POLICY": "policy.json",
            "AGENT_SCOPE_BASE_REF": "HEAD^",
            "AGENT_SCOPE_HEAD_REF": "HEAD",
            "AGENT_SCOPE_OUTPUT_FORMAT": "json",
        }
    )
    return subprocess.run(
        [sys.executable, str(ACTION_ENTRYPOINT)],
        cwd=directory,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _verify_allowed_change() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repository = Path(temporary)
        _initialize_repository(
            repository,
            {
                "allowed_paths": ["src/**", "tests/**"],
                "required_paths": ["tests/**"],
            },
        )
        Path(repository, "src", "app.py").write_text(
            "VALUE = 2\n",
            encoding="utf-8",
        )
        test_file = Path(repository, "tests", "test_app.py")
        test_file.parent.mkdir()
        test_file.write_text("# synthetic test\n", encoding="utf-8")
        _git(repository, "add", "src/app.py", "tests/test_app.py")
        _git(repository, "commit", "--quiet", "-m", "allowed")

        result = _run_action(repository)
        payload = json.loads(result.stdout)
        if result.returncode != 0 or not payload.get("ok"):
            raise RuntimeError("allowed change did not pass")


def _verify_denied_change() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repository = Path(temporary)
        _initialize_repository(
            repository,
            {
                "allowed_paths": ["**"],
                "denied_paths": ["**/*.key"],
            },
        )
        Path(repository, "deploy.key").write_text(
            "synthetic-placeholder\n",
            encoding="utf-8",
        )
        _git(repository, "add", "deploy.key")
        _git(repository, "commit", "--quiet", "-m", "denied")

        result = _run_action(repository)
        payload = json.loads(result.stdout)
        violations = payload.get("violations", [])
        codes = {item.get("code") for item in violations}
        if result.returncode != 1 or "denied_path" not in codes:
            raise RuntimeError("denied change was not rejected")


def main() -> int:
    """Verify success and failure behavior without external data or services."""

    try:
        _verify_allowed_change()
        _verify_denied_change()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"github action integration verification failed: {exc}", file=sys.stderr)
        return 1
    print("github action integration scenarios passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
