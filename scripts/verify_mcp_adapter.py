"""Deterministically exercise the Agent Scope Guard MCP stdio adapter."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from agent_scope_guard.mcp_server import PROTOCOL_VERSION


def _run_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _request(
    request_id: int,
    method: str,
    params: dict[str, object] | None = None,
) -> dict[str, object]:
    message: dict[str, object] = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
    }
    if params is not None:
        message["params"] = params
    return message


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        (root / "policy.json").write_text(
            json.dumps(
                {
                    "allowed_paths": ["src/**", "tests/**"],
                    "denied_paths": ["**/*.key"],
                    "required_paths": ["tests/**"],
                }
            ),
            encoding="utf-8",
        )
        (root / "README.md").write_text("synthetic repository\n", encoding="utf-8")
        _run_git(root, "init", "-q")
        _run_git(root, "config", "user.email", "mcp@example.invalid")
        _run_git(root, "config", "user.name", "MCP Verifier")
        _run_git(root, "add", ".")
        _run_git(root, "commit", "-qm", "initial")
        base_ref = _run_git(root, "rev-parse", "HEAD")

        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
        (root / "tests" / "test_app.py").write_text(
            "def test_value(): pass\n",
            encoding="utf-8",
        )
        _run_git(root, "add", ".")
        _run_git(root, "commit", "-qm", "allowed change")
        head_ref = _run_git(root, "rev-parse", "HEAD")

        messages = [
            _request(
                1,
                "initialize",
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "deterministic-verifier", "version": "1"},
                },
            ),
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
            _request(2, "tools/list"),
            _request(
                3,
                "tools/call",
                {
                    "name": "scope_check_paths",
                    "arguments": {
                        "policy": "policy.json",
                        "changed_paths": ["src/app.py", "tests/test_app.py"],
                    },
                },
            ),
            _request(
                4,
                "tools/call",
                {
                    "name": "scope_check_paths",
                    "arguments": {
                        "policy": "policy.json",
                        "changed_paths": ["src/deploy.key"],
                    },
                },
            ),
            _request(
                5,
                "tools/call",
                {
                    "name": "scope_check_git_diff",
                    "arguments": {
                        "policy": "policy.json",
                        "base_ref": base_ref,
                        "head_ref": head_ref,
                    },
                },
            ),
            _request(
                6,
                "tools/call",
                {
                    "name": "scope_check_paths",
                    "arguments": {
                        "policy": "../outside.json",
                        "changed_paths": ["src/app.py"],
                    },
                },
            ),
        ]
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_scope_guard.mcp_server",
                "--repo-root",
                str(root),
            ],
            input="".join(json.dumps(message) + "\n" for message in messages),
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=REPOSITORY_ROOT,
            check=True,
        )

    if completed.stderr:
        raise AssertionError("MCP server wrote unexpected stderr output")
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    if [response["id"] for response in responses] != [1, 2, 3, 4, 5, 6]:
        raise AssertionError("MCP responses did not preserve request IDs")
    if responses[0]["result"]["protocolVersion"] != PROTOCOL_VERSION:
        raise AssertionError("MCP protocol negotiation failed")
    tool_names = [
        tool["name"] for tool in responses[1]["result"]["tools"]
    ]
    if tool_names != ["scope_check_paths", "scope_check_git_diff"]:
        raise AssertionError("unexpected MCP tool inventory")
    if not responses[2]["result"]["structuredContent"]["ok"]:
        raise AssertionError("allowed explicit paths were rejected")
    if responses[3]["result"]["structuredContent"]["ok"]:
        raise AssertionError("denied explicit path was accepted")
    if not responses[4]["result"]["structuredContent"]["ok"]:
        raise AssertionError("allowed Git diff was rejected")
    if not responses[5]["result"]["isError"]:
        raise AssertionError("escaping policy path was not a tool error")

    print("mcp scope adapter scenarios passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
