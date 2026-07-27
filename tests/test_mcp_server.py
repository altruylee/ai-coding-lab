from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_scope_guard.mcp_server import (
    MAX_TOOL_CALLS_PER_SESSION,
    PROTOCOL_VERSION,
    ScopeMcpServer,
    run_stdio,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _write_policy(root: Path) -> None:
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


def _initialized_server(root: Path) -> ScopeMcpServer:
    server = ScopeMcpServer(root)
    response = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "unit-test", "version": "1"},
            },
        }
    )
    assert response is not None
    server.handle_message(
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
    )
    return server


class ScopeMcpServerTests(unittest.TestCase):
    def test_initialize_negotiates_supported_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            server = ScopeMcpServer(temporary)
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": "init",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                }
            )

        self.assertEqual(
            response["result"]["protocolVersion"],
            PROTOCOL_VERSION,
        )
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_require_initialized_notification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            server = ScopeMcpServer(temporary)
            server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                }
            )
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                }
            )

        self.assertEqual(response["error"]["code"], -32002)

    def test_lists_two_read_only_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            server = _initialized_server(Path(temporary))
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                }
            )

        tools = response["result"]["tools"]
        self.assertEqual(
            [tool["name"] for tool in tools],
            ["scope_check_paths", "scope_check_git_diff"],
        )
        self.assertTrue(
            all(tool["annotations"]["readOnlyHint"] for tool in tools)
        )

    def test_explicit_paths_return_structured_scope_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            server = _initialized_server(root)
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_paths",
                        "arguments": {
                            "policy": "policy.json",
                            "changed_paths": [
                                "src/app.py",
                                "tests/test_app.py",
                            ],
                        },
                    },
                }
            )

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertTrue(result["structuredContent"]["ok"])
        self.assertEqual(
            json.loads(result["content"][0]["text"]),
            result["structuredContent"],
        )

    def test_scope_violation_is_successful_tool_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            server = _initialized_server(root)
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_paths",
                        "arguments": {
                            "policy": "policy.json",
                            "changed_paths": ["src/deploy.key"],
                        },
                    },
                }
            )

        result = response["result"]
        self.assertFalse(result["isError"])
        self.assertFalse(result["structuredContent"]["ok"])
        codes = {
            violation["code"]
            for violation in result["structuredContent"]["violations"]
        }
        self.assertEqual(codes, {"denied_path", "required_path_missing"})

    def test_invalid_policy_path_is_tool_execution_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            server = _initialized_server(Path(temporary))
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_paths",
                        "arguments": {
                            "policy": "../private.json",
                            "changed_paths": ["src/app.py"],
                        },
                    },
                }
            )

        result = response["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(
            result["structuredContent"]["error"]["code"],
            "tool_input_error",
        )

    def test_unknown_tool_is_protocol_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            server = _initialized_server(Path(temporary))
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {"name": "write_files", "arguments": {}},
                }
            )

        self.assertEqual(response["error"]["code"], -32602)

    def test_session_tool_call_limit_returns_execution_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            server = _initialized_server(root)
            server._tool_calls = MAX_TOOL_CALLS_PER_SESSION
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_paths",
                        "arguments": {
                            "policy": "policy.json",
                            "changed_paths": ["src/app.py"],
                        },
                    },
                }
            )

        result = response["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(
            result["structuredContent"]["error"]["code"],
            "rate_limit_exceeded",
        )

    def test_git_revision_starting_with_option_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            server = _initialized_server(root)
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_git_diff",
                        "arguments": {
                            "policy": "policy.json",
                            "base_ref": "--output=/tmp/result",
                        },
                    },
                }
            )

        result = response["result"]
        self.assertTrue(result["isError"])
        self.assertIn(
            "invalid Git revision",
            result["structuredContent"]["error"]["message"],
        )

    def test_git_diff_tool_checks_only_changed_path_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            (root / "README.md").write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "MCP Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial"],
                cwd=root,
                check=True,
            )
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
            (root / "tests" / "test_app.py").write_text(
                "def test_value(): pass\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "allowed change"],
                cwd=root,
                check=True,
            )
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            server = _initialized_server(root)
            response = server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "scope_check_git_diff",
                        "arguments": {
                            "policy": "policy.json",
                            "base_ref": base,
                            "head_ref": head,
                        },
                    },
                }
            )

        payload = response["result"]["structuredContent"]
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["changed_paths"],
            ["src/app.py", "tests/test_app.py"],
        )

    def test_stdio_emits_one_json_message_per_line(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            requests = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                },
            ]
            input_stream = io.StringIO(
                "".join(json.dumps(request) + "\n" for request in requests)
            )
            output_stream = io.StringIO()
            run_stdio(
                ScopeMcpServer(root),
                input_stream,
                output_stream,
            )

        lines = output_stream.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual([json.loads(line)["id"] for line in lines], [1, 2])

    def test_module_entrypoint_keeps_stdout_protocol_clean(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_policy(root)
            requests = [
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                },
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                },
            ]
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_scope_guard.mcp_server",
                    "--repo-root",
                    str(root),
                ],
                input="".join(json.dumps(request) + "\n" for request in requests),
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

        lines = completed.stdout.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(json.loads(lines[1])["id"], 2)

    def test_packaged_console_entrypoint_is_published(self) -> None:
        pyproject = (REPOSITORY_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'agent-scope-guard-mcp = "agent_scope_guard.mcp_server:main"',
            pyproject,
        )


if __name__ == "__main__":
    unittest.main()
