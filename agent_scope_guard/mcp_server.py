"""Minimal, read-only MCP stdio adapter for Agent Scope Guard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import IO, Any, Mapping, Sequence

from . import __version__
from .policy import (
    PolicyError,
    evaluate_paths,
    load_policy,
    normalize_changed_path,
    violations_as_dicts,
)


PROTOCOL_VERSION = "2025-11-25"
MAX_MESSAGE_BYTES = 1024 * 1024
MAX_CHANGED_PATHS = 10_000
MAX_TOOL_CALLS_PER_SESSION = 1_000
_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@{}~^+-]{0,255}$")

_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "changed_paths": {
            "type": "array",
            "items": {"type": "string"},
        },
        "violations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "path": {"type": "string"},
                    "pattern": {"type": ["string", "null"]},
                    "message": {"type": "string"},
                },
                "required": ["code", "path", "pattern", "message"],
                "additionalProperties": False,
            },
        },
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["code", "message"],
            "additionalProperties": False,
        },
    },
    "required": ["ok"],
    "additionalProperties": False,
}

TOOLS: tuple[dict[str, object], ...] = (
    {
        "name": "scope_check_paths",
        "title": "Check explicit changed paths",
        "description": (
            "Evaluate repository-relative changed paths against an Agent Scope "
            "Guard policy. This tool reads only the policy file."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "policy": {
                    "type": "string",
                    "description": "Repository-relative path to a JSON policy.",
                },
                "changed_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "Repository-relative paths to evaluate.",
                },
            },
            "required": ["policy", "changed_paths"],
            "additionalProperties": False,
        },
        "outputSchema": _OUTPUT_SCHEMA,
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "scope_check_git_diff",
        "title": "Check a Git diff",
        "description": (
            "List changed path names in a local Git comparison and evaluate "
            "them against an Agent Scope Guard policy. Source contents are not read."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "policy": {
                    "type": "string",
                    "description": "Repository-relative path to a JSON policy.",
                },
                "base_ref": {
                    "type": "string",
                    "description": "Base Git revision.",
                },
                "head_ref": {
                    "type": "string",
                    "default": "HEAD",
                    "description": "Head Git revision; defaults to HEAD.",
                },
            },
            "required": ["policy", "base_ref"],
            "additionalProperties": False,
        },
        "outputSchema": _OUTPUT_SCHEMA,
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
)


class ToolInputError(ValueError):
    """Raised for invalid MCP tool arguments."""


def _jsonrpc_result(request_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _jsonrpc_error(
    request_id: object,
    code: int,
    message: str,
    data: object | None = None,
) -> dict[str, object]:
    error: dict[str, object] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _tool_result(payload: Mapping[str, object], *, is_error: bool) -> dict[str, object]:
    rendered = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "content": [{"type": "text", "text": rendered}],
        "structuredContent": dict(payload),
        "isError": is_error,
    }


def _require_object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ToolInputError(f"{label} must be an object")
    return value


def _reject_unknown(
    arguments: Mapping[str, object],
    allowed: set[str],
) -> None:
    unknown = sorted(set(arguments) - allowed)
    if unknown:
        raise ToolInputError(f"unknown argument(s): {', '.join(unknown)}")


def _require_string(
    arguments: Mapping[str, object],
    name: str,
    *,
    default: str | None = None,
) -> str:
    value = arguments.get(name, default)
    if not isinstance(value, str) or not value.strip():
        raise ToolInputError(f"{name} must be a non-empty string")
    return value.strip()


class ScopeMcpServer:
    """Handle the read-only MCP subset exposed by Agent Scope Guard."""

    def __init__(self, repo_root: str | Path) -> None:
        root = Path(repo_root).resolve()
        if not root.is_dir():
            raise ValueError(f"repository root is not a directory: {root}")
        self.repo_root = root
        self._initialize_seen = False
        self._initialized = False
        self._tool_calls = 0

    def handle_message(
        self,
        message: object,
    ) -> dict[str, object] | None:
        """Handle one decoded JSON-RPC message."""

        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return _jsonrpc_error(None, -32600, "Invalid Request")

        method = message.get("method")
        if not isinstance(method, str):
            return _jsonrpc_error(message.get("id"), -32600, "Invalid Request")

        if "id" not in message:
            self._handle_notification(method)
            return None

        request_id = message["id"]
        params = message.get("params", {})
        if not isinstance(params, dict):
            return _jsonrpc_error(request_id, -32602, "Invalid params")

        if method == "initialize":
            return self._initialize(request_id, params)
        if method == "ping":
            return _jsonrpc_result(request_id, {})
        if not self._initialized:
            return _jsonrpc_error(
                request_id,
                -32002,
                "Server is not initialized",
            )
        if method == "tools/list":
            return _jsonrpc_result(request_id, {"tools": list(TOOLS)})
        if method == "tools/call":
            return self._call_tool(request_id, params)
        return _jsonrpc_error(request_id, -32601, "Method not found")

    def _handle_notification(self, method: str) -> None:
        if method == "notifications/initialized" and self._initialize_seen:
            self._initialized = True

    def _initialize(
        self,
        request_id: object,
        params: Mapping[str, object],
    ) -> dict[str, object]:
        if self._initialize_seen:
            return _jsonrpc_error(
                request_id,
                -32600,
                "Initialize may only be sent once",
            )
        requested_version = params.get("protocolVersion")
        client_info = params.get("clientInfo")
        capabilities = params.get("capabilities")
        if (
            not isinstance(requested_version, str)
            or not isinstance(client_info, dict)
            or not isinstance(capabilities, dict)
        ):
            return _jsonrpc_error(request_id, -32602, "Invalid initialize params")

        self._initialize_seen = True
        return _jsonrpc_result(
            request_id,
            {
                "protocolVersion": (
                    requested_version
                    if requested_version == PROTOCOL_VERSION
                    else PROTOCOL_VERSION
                ),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": "agent-scope-guard",
                    "version": __version__,
                },
                "instructions": (
                    "Use these read-only tools to check declared path scope before "
                    "editing and again before proposing a change."
                ),
            },
        )

    def _call_tool(
        self,
        request_id: object,
        params: Mapping[str, object],
    ) -> dict[str, object]:
        name = params.get("name")
        if not isinstance(name, str):
            return _jsonrpc_error(request_id, -32602, "Tool name is required")
        if name not in {"scope_check_paths", "scope_check_git_diff"}:
            return _jsonrpc_error(
                request_id,
                -32602,
                f"Unknown tool: {name}",
            )
        if self._tool_calls >= MAX_TOOL_CALLS_PER_SESSION:
            payload = {
                "ok": False,
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": "MCP tool call limit reached for this session",
                },
            }
            return _jsonrpc_result(
                request_id,
                _tool_result(payload, is_error=True),
            )
        self._tool_calls += 1

        try:
            arguments = _require_object(params.get("arguments", {}), "arguments")
            if name == "scope_check_paths":
                payload = self._check_paths(arguments)
            else:
                payload = self._check_git_diff(arguments)
        except (PolicyError, ToolInputError, OSError) as exc:
            payload = {
                "ok": False,
                "error": {
                    "code": "tool_input_error",
                    "message": str(exc),
                },
            }
            return _jsonrpc_result(
                request_id,
                _tool_result(payload, is_error=True),
            )

        return _jsonrpc_result(
            request_id,
            _tool_result(payload, is_error=False),
        )

    def _resolve_policy(self, value: str) -> Path:
        normalized = value.strip().replace("\\", "/")
        pure_path = PurePosixPath(normalized)
        if (
            not normalized
            or pure_path.is_absolute()
            or ".." in pure_path.parts
        ):
            raise ToolInputError(
                "policy must be a repository-relative path that stays inside the repository"
            )

        candidate = (self.repo_root / Path(*pure_path.parts)).resolve()
        if not candidate.is_relative_to(self.repo_root):
            raise ToolInputError("policy resolves outside the repository")
        return candidate

    def _check_paths(
        self,
        arguments: Mapping[str, object],
    ) -> dict[str, object]:
        _reject_unknown(arguments, {"policy", "changed_paths"})
        policy_path = self._resolve_policy(
            _require_string(arguments, "policy")
        )
        raw_paths = arguments.get("changed_paths")
        if not isinstance(raw_paths, list) or not raw_paths:
            raise ToolInputError("changed_paths must be a non-empty array")
        if len(raw_paths) > MAX_CHANGED_PATHS:
            raise ToolInputError(
                f"changed_paths exceeds the {MAX_CHANGED_PATHS} path limit"
            )
        if not all(isinstance(path, str) for path in raw_paths):
            raise ToolInputError("every changed path must be a string")

        changed_paths = list(
            dict.fromkeys(normalize_changed_path(path) for path in raw_paths)
        )
        return self._evaluate(policy_path, changed_paths)

    def _check_git_diff(
        self,
        arguments: Mapping[str, object],
    ) -> dict[str, object]:
        _reject_unknown(arguments, {"policy", "base_ref", "head_ref"})
        policy_path = self._resolve_policy(
            _require_string(arguments, "policy")
        )
        base_ref = self._validated_ref(_require_string(arguments, "base_ref"))
        head_ref = self._validated_ref(
            _require_string(arguments, "head_ref", default="HEAD")
        )
        command = [
            "git",
            "-C",
            str(self.repo_root),
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            "--diff-filter=ACMR",
            "--relative",
            f"{base_ref}...{head_ref}",
        ]
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = getattr(exc, "stderr", None) or str(exc)
            raise ToolInputError(f"git diff failed: {detail.strip()}") from exc

        changed_paths = [
            normalize_changed_path(line)
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        if len(changed_paths) > MAX_CHANGED_PATHS:
            raise ToolInputError(
                f"Git diff exceeds the {MAX_CHANGED_PATHS} path limit"
            )
        return self._evaluate(policy_path, changed_paths)

    @staticmethod
    def _validated_ref(value: str) -> str:
        if not _REF_PATTERN.fullmatch(value) or "..." in value:
            raise ToolInputError(f"invalid Git revision: {value}")
        return value

    @staticmethod
    def _evaluate(
        policy_path: Path,
        changed_paths: list[str],
    ) -> dict[str, object]:
        violations = evaluate_paths(load_policy(policy_path), changed_paths)
        return {
            "ok": not violations,
            "changed_paths": changed_paths,
            "violations": violations_as_dicts(violations),
        }


def run_stdio(
    server: ScopeMcpServer,
    input_stream: IO[str],
    output_stream: IO[str],
) -> None:
    """Serve newline-delimited MCP JSON-RPC messages until stdin closes."""

    for line in input_stream:
        if len(line.encode("utf-8")) > MAX_MESSAGE_BYTES:
            response = _jsonrpc_error(None, -32600, "Message exceeds size limit")
        else:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                response = _jsonrpc_error(None, -32700, "Parse error")
            else:
                response = server.handle_message(message)

        if response is not None:
            output_stream.write(
                json.dumps(
                    response,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            output_stream.flush()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-scope-guard-mcp",
        description="Run the read-only Agent Scope Guard MCP stdio adapter.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="repository whose paths and local Git history may be checked",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MCP stdio server."""

    args = _build_parser().parse_args(argv)
    try:
        server = ScopeMcpServer(args.repo_root)
    except ValueError as exc:
        print(f"startup error: {exc}", file=sys.stderr)
        return 2
    run_stdio(server, sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
